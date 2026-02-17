# MarathiTTSv1 — Marathi Text-to-Speech

A Marathi Text-to-Speech (TTS) training pipeline using [Piper](https://github.com/rhasspy/piper) and the VITS architecture. Trained on the [OpenSLR-64](https://openslr.org/64/) Marathi dataset, designed for offline deployment on Raspberry Pi.

## Project Structure

```
MarathiTTSv1/
├── scripts/                    # All pipeline scripts
│   ├── setup_piper.sh          # One-time setup (Linux/Mac)
│   ├── format_data.py          # Data preparation (OpenSLR-64 → LJSpeech)
│   ├── normalize_marathi.py    # Marathi text normalizer (numbers, abbreviations)
│   ├── download_checkpoint.py  # Download pretrained checkpoint for fine-tuning
│   ├── train.sh                # Training script (Linux/Colab — recommended)
│   ├── train.bat               # Training script (Windows — from-scratch only)
│   ├── test_checkpoint.py      # Test a checkpoint with sample audio
│   └── export_onnx.py          # Export trained model to ONNX for Raspberry Pi
├── data/                       # Dataset (not in git)
│   ├── mr_in_female/           # Raw OpenSLR-64 audio files
│   ├── line_index.tsv          # OpenSLR-64 transcriptions
│   └── ljspeech_filtered/      # Processed LJSpeech-format dataset
├── piper_train/                # Piper training code (see Setup)
├── checkpoints/                # Pretrained checkpoints (not in git)
├── training_filtered/          # Training output, logs, checkpoints (not in git)
├── output/                     # Exported ONNX models (not in git)
├── Dockerfile.training         # Docker training environment
├── requirements.txt            # Python dependencies
└── README.md
```

## Features

- **Best Speaker Selection**: Automatically identifies and filters the most frequent speaker
- **Audio Quality Filtering**: Removes clips by duration (1–15s), RMS amplitude, and clipping detection
- **Complete Marathi Normalization**: 
  - Full 0–100 number lookup with correct compound words (e.g., 21 = एकवीस, 42 = बेचाळीस)
  - Indian numbering system: हजार, लाख, कोटी
  - Abbreviation expansion (डॉ. → डॉक्टर, इ.स. → ईसवी सन)
- **Two Training Modes**:
  - **Linux/Colab**: Fine-tune from English checkpoint using espeak-ng phonemes (faster, better quality)
  - **Windows**: Train from scratch using Devanagari characters (no espeak required)
- **Raspberry Pi Deployment**: Export to ONNX and run with Piper

## Quick Start (Linux / Google Colab)

### 1. Setup Environment

```bash
# Clone this repository
git clone <your-repo-url> MarathiTTSv1
cd MarathiTTSv1

# Run setup (installs Piper, espeak-ng, dependencies)
chmod +x scripts/setup_piper.sh
./scripts/setup_piper.sh
```

### 2. Prepare Dataset

Download and extract [OpenSLR-64](https://openslr.org/64/):

```bash
mkdir -p data
cd data
wget https://www.openslr.org/resources/64/mr_in_female.zip
unzip mr_in_female.zip
wget https://www.openslr.org/resources/64/line_index.tsv
cd ..
```

Then run data preparation:

```bash
python scripts/format_data.py
```

This will:
- Analyze all speakers and select the one with the most recordings
- Convert audio to mono 22050Hz WAV
- Filter by duration and quality
- Normalize Marathi text
- Output a clean LJSpeech-format dataset in `data/ljspeech_filtered/`

### 3. Download Checkpoint (for fine-tuning)

```bash
python scripts/download_checkpoint.py
```

### 4. Train

```bash
# Fine-tune from English checkpoint (recommended)
./scripts/train.sh

# Or train from scratch (no checkpoint needed)
./scripts/train.sh --from-scratch

# Override batch size for smaller GPUs
./scripts/train.sh --batch-size 16
```

### 5. Monitor Training

```bash
tensorboard --logdir training_filtered/lightning_logs
# Open http://localhost:6006
```

### 6. Test a Checkpoint

```bash
python scripts/test_checkpoint.py \
    training_filtered/lightning_logs/version_0/checkpoints/epoch=500-step=25000.ckpt \
    --text "नमस्कार, कसे आहात?"
```

### 7. Export for Raspberry Pi

```bash
python scripts/export_onnx.py \
    training_filtered/lightning_logs/version_0/checkpoints/epoch=999-step=50000.ckpt
```

This creates `output/marathi-medium.onnx` and `output/marathi-medium.onnx.json`.

### 8. Deploy on Raspberry Pi

```bash
# Install Piper on Pi
pip install piper-tts

# Copy model files to Pi, then:
echo "नमस्कार, कसे आहात?" | piper \
    --model marathi-medium.onnx \
    --output_file output.wav

aplay output.wav
```

## Quick Start (Windows)

> **Note:** On Windows, training uses character-level input (no espeak-ng required) and
> trains from scratch. This is slower and slightly lower quality than fine-tuning on Linux.
> For best results, use Google Colab or a Linux cloud VM.

### 1. Setup Piper Training Code

```batch
git clone https://github.com/rhasspy/piper.git piper_train_temp
xcopy /E /I piper_train_temp\src piper_train\src
rmdir /S /Q piper_train_temp

pip install -r requirements.txt
pip install torch torchaudio

cd piper_train\src\python
pip install -e .
cd ..\..\..
```

### 2. Prepare Data

Place OpenSLR-64 files in `data/mr_in_female/` and `data/line_index.tsv`, then:

```batch
python scripts\format_data.py
```

### 3. Train

```batch
scripts\train.bat
```

## Training on Google Colab

Estimated cost: **$10–$30** (fine-tuning with Colab Pro on T4)

```python
# In a Colab notebook:
!git clone <your-repo-url> MarathiTTSv1
%cd MarathiTTSv1
!chmod +x scripts/setup_piper.sh && ./scripts/setup_piper.sh

# Download OpenSLR-64
!mkdir -p data && cd data && wget -q https://www.openslr.org/resources/64/mr_in_female.zip && unzip -q mr_in_female.zip && wget -q https://www.openslr.org/resources/64/line_index.tsv && cd ..

# Prepare data
!python scripts/format_data.py

# Download checkpoint
!python scripts/download_checkpoint.py

# Train (save checkpoints to Google Drive for persistence)
!./scripts/train.sh
```

## Important Notes

### Phoneme Type vs. Checkpoint Compatibility

- **Linux (espeak phonemes)**: Can fine-tune from the English Lessac checkpoint → faster training, better quality
- **Windows (text/character mode)**: Must train from scratch — the English checkpoint uses IPA phonemes which are incompatible with Devanagari character tokens

### Training Duration Guide

| Scenario | GPU | Estimated Time | Estimated Cost (Colab) |
|----------|-----|---------------|----------------------|
| Fine-tune, ~1K utterances | T4 | 8–12 hrs | $10–15 |
| Fine-tune, ~3K utterances | T4 | 15–24 hrs | $20–30 |
| From scratch, ~3K utterances | T4 | 48–72 hrs | $60–85 |

### Tips for Natural-Sounding Output

1. **Dataset quality > quantity**: Clean audio from one consistent speaker beats a large noisy dataset
2. **Length scale**: At inference, use `--length-scale 1.1` to `1.3` for more natural pacing
3. **Monitor validation loss**: Stop training when it plateaus (avoid overfitting)
4. **Test frequently**: Use `test_checkpoint.py` every ~100 epochs to track quality

## License

Dataset: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) (OpenSLR-64)  
Piper: [MIT License](https://github.com/rhasspy/piper/blob/master/LICENSE)
