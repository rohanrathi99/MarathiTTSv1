import os
import csv
import librosa
import soundfile as sf
from tqdm import tqdm
import concurrent.futures

# Paths
DATA_ROOT = r"d:\WorkStation\PlayGrounds\PlayGround-8\AiAntargyanV2\data"
SOURCE_WAVS = os.path.join(DATA_ROOT, "mr_in_female")
TRANSCRIPT_FILE = os.path.join(DATA_ROOT, "line_index.tsv")
OUTPUT_WAVS = os.path.join(DATA_ROOT, "wavs")
OUTPUT_METADATA = os.path.join(DATA_ROOT, "metadata.csv")

# Audio Config
TARGET_SR = 22050

def process_audio(filename, source_path, target_path):
    try:
        # Load audio (librosa handles resampling and mono conversion)
        y, sr = librosa.load(source_path, sr=TARGET_SR, mono=True)
        # Save as WAV
        sf.write(target_path, y, sr)
        return True
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return False

def main():
    os.makedirs(OUTPUT_WAVS, exist_ok=True)

    # Read transcripts
    transcripts = []
    if not os.path.exists(TRANSCRIPT_FILE):
        print(f"Transcript file not found: {TRANSCRIPT_FILE}")
        return

    print("Reading transcripts...")
    with open(TRANSCRIPT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if len(row) >= 2:
                filename = row[0]
                raw_text = row[1]
                try:
                    from normalize_marathi import normalize_text
                    text = normalize_text(raw_text)
                except ImportError:
                     print("Warning: normalize_marathi not found, using raw text")
                     text = raw_text
                transcripts.append((filename, text))

    print(f"Found {len(transcripts)} items.")

    # Process files
    valid_entries = []
    
    # We will use a ThreadPool for faster I/O processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for filename, text in transcripts:
            # Check if source file exists. 
            # OpenSLR usually has .wav extension in the file system but maybe not in the TSV filename column?
            # Based on previous `ls`, files start with `mrt_`. 
            # I'll Assume TSV has just the ID `mrt_xxxxx` or `mrt_xxxxx.wav`.
            # Let's check for both.
            
            src_file = os.path.join(SOURCE_WAVS, filename)
            if not os.path.exists(src_file):
                 src_file = os.path.join(SOURCE_WAVS, filename + ".wav")
            
            if os.path.exists(src_file):
                dst_file = os.path.join(OUTPUT_WAVS, filename + ".wav")
                if not os.path.exists(dst_file):
                    futures.append(executor.submit(process_audio, filename, src_file, dst_file))
                # Always append to valid entries for metadata
                valid_entries.append((filename, text))
            else:
                # print(f"File not found: {filename}")
                pass

        # Wait for all to complete
        for _ in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing Audio"):
            pass

    # Write metadata
    print("Writing metadata.csv...")
    with open(OUTPUT_METADATA, 'w', encoding='utf-8', newline='') as f:
        # Piper expects: filename|text
        writer = csv.writer(f, delimiter='|', quotechar=None)
        for filename, text in valid_entries:
            writer.writerow([filename, text])

    print("Done!")

if __name__ == "__main__":
    main()
