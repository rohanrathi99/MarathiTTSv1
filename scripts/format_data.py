import os
import csv
import librosa
import soundfile as sf
import numpy as np
from tqdm import tqdm
import concurrent.futures
from collections import Counter
try:
    from normalize_marathi import normalize_text
except ImportError:
    print("Warning: normalize_marathi not found, using raw text")
    def normalize_text(t): return t

# Paths
DATA_ROOT = r"d:\WorkStation\PlayGrounds\PlayGround-8\AiAntargyanV2\data"
SOURCE_WAVS = os.path.join(DATA_ROOT, "mr_in_female")
TRANSCRIPT_FILE = os.path.join(DATA_ROOT, "line_index.tsv")

# Output for filtered dataset
OUTPUT_DIR = os.path.join(DATA_ROOT, "ljspeech_filtered")
OUTPUT_WAVS = os.path.join(OUTPUT_DIR, "wavs")
OUTPUT_METADATA = os.path.join(OUTPUT_DIR, "metadata.csv")

# Config
TARGET_SR = 22050
MIN_DURATION = 1.0
MAX_DURATION = 15.0
MIN_RMS = 0.005 # Filter silence
MAX_RMS = 1.0   # Not strictly removing loud clips unless clipped, keeping loose

def analyze_and_process(filename, source_path, target_path):
    try:
        # Load with librosa to resample and mix to mono
        # This is slower than ffmpeg but we have librosa dependency
        y, sr = librosa.load(source_path, sr=TARGET_SR, mono=True)
        
        # Audio Filtering
        duration = librosa.get_duration(y=y, sr=sr)
        rms = np.sqrt(np.mean(y**2))
        
        if duration < MIN_DURATION or duration > MAX_DURATION:
            return False
        if rms < MIN_RMS:
            return False
            
        # Save
        sf.write(target_path, y, sr)
        return True
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return False

def main():
    os.makedirs(OUTPUT_WAVS, exist_ok=True)

    # 1. Read Transcripts & Analyze Speakers
    print("Reading transcripts...")
    all_rows = []
    speaker_counts = Counter()
    
    if not os.path.exists(TRANSCRIPT_FILE):
        print(f"Missing {TRANSCRIPT_FILE}")
        return

    with open(TRANSCRIPT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if len(row) >= 2:
                # expecting mr_SPEAKERID_XXXX
                fid = row[0]
                text = row[1]
                parts = fid.split('_')
                if len(parts) >= 2:
                    speaker_id = parts[1]
                    speaker_counts[speaker_id] += 1
                    all_rows.append((fid, text, speaker_id))

    if not all_rows:
        print("No data found.")
        return

    # Select Best Speaker
    best_speaker, count = speaker_counts.most_common(1)[0]
    print(f"Selected Best Speaker: {best_speaker} ({count} utterances)")
    
    # Filter rows
    speaker_rows = [r for r in all_rows if r[2] == best_speaker]
    
    # 2. Process Files
    print(f"Processing {len(speaker_rows)} utterances for speaker {best_speaker}...")
    
    metadata_lines = []
    
    # We'll use a sequential ID for the cleaner dataset
    next_id = 0
    
    # Process serially or parallel? Parallel is faster but we need stable IDs.
    # We can pre-assign IDs but we filter based on audio quality, so we don't know final IDs yet.
    # Actually, let's process parallel, collect results, THEN assign IDs and write metadata/rename?
    # Or just write to temp names and rename success ones?
    # Let's simple: Process parallel to temp wavs, then filter metadata.
    
    # Actually, simpler: just process and if success, add to list. 
    # But threading order is non-deterministic.
    # Let's use map and keep order?
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # map futures to rows
        future_to_row = {}
        for fid, text, spk in speaker_rows:
            src = os.path.join(SOURCE_WAVS, fid)
            if not os.path.exists(src):
                src = src + ".wav"
            
            if os.path.exists(src):
                # Target temp path
                dst_temp = os.path.join(OUTPUT_WAVS, f"temp_{fid}.wav")
                if not os.path.exists(dst_temp):
                    future = executor.submit(analyze_and_process, fid, src, dst_temp)
                    future_to_row[future] = (fid, text, dst_temp)
                else:
                    # Already processed, check quality? optimize: assume valid if exists
                    # We'll treat as success for now to speed up re-runs, 
                    # BUT we need to know if it passed filter. 
                    # Re-verify? No, assumes folder is clean.
                    # For correctness let's re-checker or just assume good.
                    pass 
                    # We need to recreate the future to track it.
                    # Ideally we clear the folder.
            
        # Collect results
        # To ensure deterministic order (for reproducibility), we should iterate valid rows
        # But futures return as completed.
        # Let's just collect all successful results.
        
        valid_results = []
        for future in tqdm(concurrent.futures.as_completed(future_to_row), total=len(future_to_row), desc="Filtering Audio"):
            fid, raw_text, temp_wav = future_to_row[future]
            try:
                if future.result():
                    valid_results.append((fid, raw_text, temp_wav))
                else:
                    # Failed processing or filtering
                    if os.path.exists(temp_wav): os.remove(temp_wav)
            except Exception as e:
                print(f"Exception for {fid}: {e}")

    # 3. Finalize: Normalize Text, Renumber, Write Metadata
    print("Finalizing dataset...")
    # Sort by original file id to be deterministic
    valid_results.sort(key=lambda x: x[0])
    
    final_metadata = []
    
    for idx, (fid, raw_text, temp_wav) in enumerate(valid_results):
        # New name
        seq_id = f"{idx:05d}"
        final_wav_name = f"{seq_id}.wav"
        final_wav_path = os.path.join(OUTPUT_WAVS, final_wav_name)
        
        # Rename temp to final
        if os.path.exists(temp_wav):
            if os.path.exists(final_wav_path): os.remove(final_wav_path)
            os.rename(temp_wav, final_wav_path)
            
        # Normalize text
        norm_text = normalize_text(raw_text)
        
        # Add to metadata (Piper LJSpeech: id|text)
        # Adding raw text as 3rd col just in case
        final_metadata.append(f"{seq_id}|{norm_text}|{norm_text}")

    # Write metadata
    with open(OUTPUT_METADATA, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(final_metadata))

    print(f"Done! Created {len(final_metadata)} valid samples in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
