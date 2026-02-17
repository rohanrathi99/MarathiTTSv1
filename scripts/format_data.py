"""
Format OpenSLR-64 Marathi dataset into LJSpeech format for Piper TTS training.

FIXED: Relative paths (no hardcoded Windows paths)
FIXED: normalize_marathi import (uses sys.path)
FIXED: Re-run bug (cleans output dir on each run)
FIXED: MAX_RMS threshold (0.5 instead of 1.0)
"""
import os
import sys
import csv
import shutil
import numpy as np
from tqdm import tqdm
import concurrent.futures
from collections import Counter

# Fix import path so normalize_marathi can be found
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from normalize_marathi import normalize_text

# Paths — relative to project root
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_ROOT = os.path.join(PROJECT_ROOT, "data")
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
MIN_RMS = 0.005   # Filter silence
MAX_RMS = 0.5     # Filter clipped/distorted audio

# Lazy imports for audio (so script shows errors early for path issues)
librosa = None
sf = None


def _ensure_audio_libs():
    global librosa, sf
    if librosa is None:
        import librosa as _librosa
        import soundfile as _sf
        librosa = _librosa
        sf = _sf


def analyze_and_process(filename, source_path, target_path):
    """Load, resample, filter, and save a single audio file."""
    _ensure_audio_libs()
    try:
        y, sr = librosa.load(source_path, sr=TARGET_SR, mono=True)

        # Audio Filtering
        duration = librosa.get_duration(y=y, sr=sr)
        rms = np.sqrt(np.mean(y ** 2))

        if duration < MIN_DURATION or duration > MAX_DURATION:
            return False
        if rms < MIN_RMS or rms > MAX_RMS:
            return False

        # Save
        sf.write(target_path, y, sr)
        return True
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return False


def main():
    # Validate source data exists
    if not os.path.exists(TRANSCRIPT_FILE):
        print(f"ERROR: Missing transcript file: {TRANSCRIPT_FILE}")
        print(f"Make sure you've extracted OpenSLR-64 into: {DATA_ROOT}/mr_in_female/")
        return

    if not os.path.exists(SOURCE_WAVS):
        print(f"ERROR: Missing source audio directory: {SOURCE_WAVS}")
        return

    # Clean output directory for reproducible results
    if os.path.exists(OUTPUT_DIR):
        print(f"Cleaning previous output: {OUTPUT_DIR}")
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_WAVS, exist_ok=True)

    # 1. Read Transcripts & Analyze Speakers
    print("Reading transcripts...")
    all_rows = []
    speaker_counts = Counter()

    with open(TRANSCRIPT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if len(row) >= 2:
                fid = row[0].strip()
                text = row[1].strip()
                parts = fid.split('_')
                if len(parts) >= 2:
                    speaker_id = parts[1]
                    speaker_counts[speaker_id] += 1
                    all_rows.append((fid, text, speaker_id))

    if not all_rows:
        print("No data found in transcript file.")
        return

    # Display speaker distribution
    print(f"\n=== Speaker Distribution (top 10) ===")
    for spk, count in speaker_counts.most_common(10):
        print(f"  Speaker {spk}: {count} utterances")

    # Select Best Speaker
    best_speaker, count = speaker_counts.most_common(1)[0]
    print(f"\nSelected Best Speaker: {best_speaker} ({count} utterances)")

    # Filter rows
    speaker_rows = [r for r in all_rows if r[2] == best_speaker]

    # 2. Process Files
    print(f"\nProcessing {len(speaker_rows)} utterances for speaker {best_speaker}...")

    valid_results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_row = {}
        skipped_missing = 0

        for fid, text, spk in speaker_rows:
            src = os.path.join(SOURCE_WAVS, fid)
            if not src.endswith('.wav'):
                src = src + ".wav"

            if not os.path.exists(src):
                skipped_missing += 1
                continue

            dst = os.path.join(OUTPUT_WAVS, f"temp_{fid}.wav")
            future = executor.submit(analyze_and_process, fid, src, dst)
            future_to_row[future] = (fid, text, dst)

        if skipped_missing:
            print(f"  Skipped {skipped_missing} files (audio not found)")

        # Collect results
        for future in tqdm(concurrent.futures.as_completed(future_to_row),
                           total=len(future_to_row), desc="Filtering Audio"):
            fid, raw_text, temp_wav = future_to_row[future]
            try:
                if future.result():
                    valid_results.append((fid, raw_text, temp_wav))
                else:
                    if os.path.exists(temp_wav):
                        os.remove(temp_wav)
            except Exception as e:
                print(f"Exception for {fid}: {e}")

    # 3. Finalize: Normalize Text, Renumber, Write Metadata
    print("\nFinalizing dataset...")

    # Sort by original file id for deterministic ordering
    valid_results.sort(key=lambda x: x[0])

    final_metadata = []
    normalization_errors = 0

    for idx, (fid, raw_text, temp_wav) in enumerate(valid_results):
        seq_id = f"{idx:05d}"
        final_wav_path = os.path.join(OUTPUT_WAVS, f"{seq_id}.wav")

        # Rename temp to final
        if os.path.exists(temp_wav):
            os.rename(temp_wav, final_wav_path)

        # Normalize text
        try:
            norm_text = normalize_text(raw_text)
        except Exception as e:
            print(f"  Normalization error for {fid}: {e}")
            norm_text = raw_text
            normalization_errors += 1

        if not norm_text or len(norm_text.strip()) < 2:
            # Skip empty/trivial normalizations
            if os.path.exists(final_wav_path):
                os.remove(final_wav_path)
            continue

        # LJSpeech format: id|text|text
        final_metadata.append(f"{seq_id}|{norm_text}|{norm_text}")

    # Write metadata
    with open(OUTPUT_METADATA, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(final_metadata))

    # Summary
    print(f"\n=== Dataset Creation Complete ===")
    print(f"  Valid samples:          {len(final_metadata)}")
    print(f"  Filtered out:           {len(speaker_rows) - len(final_metadata)}")
    print(f"  Normalization warnings:  {normalization_errors}")
    print(f"  Output directory:       {OUTPUT_DIR}")
    print(f"  Metadata file:          {OUTPUT_METADATA}")


if __name__ == "__main__":
    main()
