# MarathiTTSv1 — Complete Step-by-Step Guide

> **Platform:** This guide covers **Windows** (primary), **Linux/macOS**, and **Google Colab**.  
> **Goal:** Take you from zero to a running Marathi TTS model, with every command you need.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)  
2. [Project Structure](#2-project-structure)  
3. [Windows Setup (Recommended for Most Users)](#3-windows-setup)  
   - 3.1 [Create Virtual Environment](#31-create-virtual-environment)  
   - 3.2 [Install PyTorch](#32-install-pytorch)  
   - 3.3 [Run Automated Setup](#33-run-automated-setup)  
   - 3.4 [Fix pkg_resources Error](#34-fix-pkg_resources-error-python-312-only)  
4. [Linux / macOS Setup](#4-linux--macos-setup)  
5. [Google Colab Setup](#5-google-colab-setup)  
6. [Dataset Download & Preparation](#6-dataset-download--preparation)  
7. [Running Training](#7-running-training)  
8. [Monitoring Training](#8-monitoring-training)  
9. [Testing a Checkpoint](#9-testing-a-checkpoint)  
10. [Exporting for Raspberry Pi](#10-exporting-for-raspberry-pi)  
11. [Deploying on Raspberry Pi](#11-deploying-on-raspberry-pi)  
12. [Troubleshooting](#12-troubleshooting)  
13. [Training Tips](#13-training-tips)  

---

## 1. Prerequisites

### Windows
| Requirement | Version | How to Check |
|---|---|---|
| Python | 3.10 – 3.12 | `python --version` |
| Git | Any | `git --version` |
| NVIDIA GPU | RTX 20xx+ recommended | Device Manager → Display Adapters |
| CUDA Toolkit | 11.8 or 12.4 | `nvcc --version` |
| (Optional) MSVC C++ Build Tools | 14.0+ | Needed to compile monotonic_align extension |

> **No GPU?** Training will use CPU. It will be ~20-50x slower but still works.

### Linux / macOS
| Requirement | Version |
|---|---|
| Python | 3.10 – 3.12 |
| espeak-ng | Any (with Marathi `mr` language support) |
| CUDA | 11.8 or 12.1+ |

---

## 2. Project Structure

```
MarathiTTSv1/
├── scripts/
│   ├── setup_piper.bat         ← Windows one-click setup (NEW)
│   ├── setup_piper.sh          ← Linux/macOS one-click setup
│   ├── fix_environment.bat     ← Fixes pkg_resources error (NEW)
│   ├── train.bat               ← Windows training (FIXED: pre-flight checks)
│   ├── train.sh                ← Linux/Colab training
│   ├── format_data.py          ← Data preparation
│   ├── normalize_marathi.py    ← Text normalizer (FIXED: decimals, dates, ordinals)
│   ├── download_dataset.py     ← Automated dataset download
│   ├── download_checkpoint.py  ← Download English fine-tune checkpoint
│   ├── test_checkpoint.py      ← Generate audio from any checkpoint
│   └── export_onnx.py          ← Export to ONNX for Raspberry Pi
├── piper_train/                ← Cloned by setup script (not in git)
├── data/                       ← Dataset files (not in git)
├── training_filtered/          ← Training output (not in git)
├── checkpoints/                ← Pretrained models (not in git)
├── output/                     ← ONNX exports (not in git)
├── requirements.txt            ← Python dependencies (FIXED: version conflict resolved)
├── Dockerfile.training         ← Docker GPU training environment
└── STEP_BY_STEP_GUIDE.md       ← This file
```

---

## 3. Windows Setup

Open **PowerShell** or **Command Prompt** and `cd` to the project root.

### 3.1 Create Virtual Environment

```powershell
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your prompt after activation.

### 3.2 Install PyTorch

Choose the command that matches your GPU:

```powershell
# RTX 30xx / 40xx (CUDA 12.4) — recommended
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

# RTX 20xx / older (CUDA 11.8)
pip install torch torchaudio --extra-index-url https://download.pytorch.org/whl/cu118

# No GPU (CPU only — slow but works)
pip install torch torchaudio
```

Verify CUDA is detected:
```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available(), '| Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

### 3.3 Run Automated Setup

This single script handles everything: cloning piper, installing dependencies, building the C extension, and verifying imports.

```powershell
scripts\setup_piper.bat
```

What it does step-by-step:
1. Creates the venv if not present
2. Upgrades pip, setuptools, wheel
3. Installs PyTorch (CUDA 12.4 by default)
4. Installs all packages from `requirements.txt`
5. Clones `rhasspy/piper` from GitHub into `piper_train/`
6. Installs `piper_train` in editable mode
7. Attempts to build the `monotonic_align` C extension (falls back to Numba)
8. Calls `fix_environment.bat` to verify everything works
9. Prints a self-test report

If all lines show `OK`, setup is complete. Jump to [Section 6](#6-dataset-download--preparation).

### 3.4 Fix pkg_resources Error (Python 3.12 only)

If you see:
```
ModuleNotFoundError: No module named 'pkg_resources'
```

Run:
```powershell
scripts\fix_environment.bat
```

**Why this happens:** Python 3.12 stopped auto-including `setuptools` in virtual environments. The `pkg_resources` module lives inside `setuptools`. Versions of `lightning_fabric` below 2.3 import `pkg_resources` at startup and crash. The fix script installs `setuptools` and upgrades `pytorch-lightning` to 2.4+ (which removed the `pkg_resources` dependency entirely).

---

## 4. Linux / macOS Setup

```bash
# Clone repo and enter directory
cd MarathiTTSv1

# Run one-time setup
chmod +x scripts/setup_piper.sh
./scripts/setup_piper.sh

# Verify espeak-ng has Marathi support
espeak-ng --voices | grep " mr "
```

If Marathi is not listed by espeak-ng, build from source:
```bash
git clone https://github.com/espeak-ng/espeak-ng.git
cd espeak-ng
./autogen.sh && ./configure && make && sudo make install
```

---

## 5. Google Colab Setup

Create a new Colab notebook and run each cell:

**Cell 1 — Clone and setup:**
```python
!git clone <your-repo-url> MarathiTTSv1
%cd MarathiTTSv1
!chmod +x scripts/setup_piper.sh
!./scripts/setup_piper.sh
```

**Cell 2 — Download dataset:**
```python
!python scripts/download_dataset.py
```

**Cell 3 — Prepare data:**
```python
!python scripts/format_data.py
```

**Cell 4 — Download English checkpoint for fine-tuning:**
```python
!python scripts/download_checkpoint.py
```

**Cell 5 — Train:**
```python
!./scripts/train.sh
```

> **Cost estimate:** $10–$30 with Colab Pro (T4 GPU, fine-tuning mode).  
> **Tip:** Mount Google Drive and point checkpoints there so they survive session restarts.

---

## 6. Dataset Download & Preparation

### Option A — Automated Download (recommended)

```powershell
# Windows
python scripts\download_dataset.py

# Linux/macOS
python scripts/download_dataset.py
```

This downloads `mr_in_female.zip` (~300 MB) and `line_index.tsv` from OpenSLR-64 automatically.

### Option B — Manual Download

1. Go to: https://openslr.org/64/
2. Download `mr_in_female.zip` → extract to `data\mr_in_female\`
3. Download `line_index.tsv` → save to `data\line_index.tsv`

Your `data\` folder should look like:
```
data/
├── mr_in_female/
│   ├── mr_in_female_SPEAKER1_00001.wav
│   ├── mr_in_female_SPEAKER1_00002.wav
│   └── ...
└── line_index.tsv
```

### Prepare the Dataset

```powershell
python scripts\format_data.py
```

This script will:
- Analyse all speakers and select the one with the most recordings
- Convert audio to mono 22,050 Hz WAV
- Filter clips by duration (1–15 s), silence (RMS < 0.005), and clipping (RMS > 0.5)
- Expand Marathi abbreviations and convert numbers to words
- Output a clean LJSpeech-format dataset to `data\ljspeech_filtered\`

Expected output:
```
=== Speaker Distribution (top 10) ===
  Speaker 0001: 280 utterances
  ...

Selected Best Speaker: 0001 (280 utterances)
Processing 280 utterances...

=== Dataset Creation Complete ===
  Valid samples:    250
  Filtered out:     30
  Output directory: data/ljspeech_filtered
```

---

## 7. Running Training

### Windows (from scratch — text mode)

```powershell
scripts\train.bat
```

Override batch size if you run out of GPU memory:
```powershell
scripts\train.bat --batch-size 4
```

### Linux / macOS (fine-tuning — recommended)

Download the English checkpoint first:
```bash
python scripts/download_checkpoint.py
```

Then train:
```bash
# Fine-tune from English checkpoint (faster, better quality)
./scripts/train.sh

# Train from scratch (no checkpoint needed)
./scripts/train.sh --from-scratch

# Override batch size for smaller GPUs
./scripts/train.sh --batch-size 16
```

### Training Mode Comparison

| | Windows (train.bat) | Linux/Colab (train.sh) |
|---|---|---|
| Phoneme type | Devanagari characters | IPA via espeak-ng |
| Starting point | From scratch | Fine-tune English checkpoint |
| Max epochs | 2,000 | 1,000 |
| Estimated time (T4) | 48–72 hrs | 8–24 hrs |
| Estimated cost (Colab) | $60–85 | $10–30 |
| Output quality | Good | Better |

---

## 8. Monitoring Training

Open a **second terminal** and run:

```powershell
# Windows
venv\Scripts\tensorboard --logdir training_filtered\lightning_logs

# Linux/macOS
source venv/bin/activate
tensorboard --logdir training_filtered/lightning_logs
```

Open your browser at: **http://localhost:6006**

Key metrics to watch:
- `train_loss` — should decrease steadily
- `val_loss` — should track train_loss; if it diverges upward, you may be overfitting
- Stop training when `val_loss` plateaus for 100+ epochs

---

## 9. Testing a Checkpoint

You can generate audio from any checkpoint during training to evaluate quality:

```powershell
# Windows
python scripts\test_checkpoint.py ^
    training_filtered\lightning_logs\version_0\checkpoints\epoch=500-step=25000.ckpt ^
    --text "नमस्कार, कसे आहात?"

# Linux/macOS
python scripts/test_checkpoint.py \
    training_filtered/lightning_logs/version_0/checkpoints/epoch=500-step=25000.ckpt \
    --text "नमस्कार, कसे आहात?"
```

Options:
- `--text "..."` — Marathi text to synthesise
- `--length-scale 1.2` — Slow speech slightly (1.1–1.3 recommended for Marathi)
- `--output-dir test_output/` — Where to save the WAV file

> **Tip:** Test every ~100 epochs. Quality jumps are usually audible by epoch 200–400.

---

## 10. Exporting for Raspberry Pi

Once training is complete, export your best checkpoint to ONNX:

```powershell
# Windows
python scripts\export_onnx.py ^
    training_filtered\lightning_logs\version_0\checkpoints\epoch=999-step=50000.ckpt

# Linux/macOS
python scripts/export_onnx.py \
    training_filtered/lightning_logs/version_0/checkpoints/epoch=999-step=50000.ckpt
```

This creates two files in `output\`:
- `marathi-medium.onnx` — the model weights
- `marathi-medium.onnx.json` — the configuration (required by piper-tts)

**Copy both files to your Raspberry Pi.**

---

## 11. Deploying on Raspberry Pi

```bash
# Install piper on the Pi
pip install piper-tts

# Test synthesis
echo "नमस्कार, कसे आहात?" | piper \
    --model marathi-medium.onnx \
    --output_file output.wav

# Play the result
aplay output.wav
```

For slower but more natural-sounding speech:
```bash
echo "नमस्कार" | piper \
    --model marathi-medium.onnx \
    --length_scale 1.2 \
    --output_file output.wav
```

---

## 12. Troubleshooting

### `ModuleNotFoundError: No module named 'pkg_resources'`

**Cause:** Python 3.12 removed `setuptools` from venvs; `lightning_fabric < 2.3` imports `pkg_resources` at startup.

**Fix:**
```powershell
scripts\fix_environment.bat
```
Or manually:
```powershell
venv\Scripts\pip install setuptools
venv\Scripts\pip install "pytorch-lightning>=2.4.0,<3.0.0"
```

---

### `CUDA out of memory`

**Fix:** Reduce batch size:
```powershell
scripts\train.bat --batch-size 4
```

---

### `ModuleNotFoundError: No module named 'piper_train'`

**Fix:** The piper_train module isn't installed. Run:
```powershell
scripts\setup_piper.bat
```

---

### `ERROR: Preprocessing failed`

**Cause:** Dataset not found or malformed.

**Fix:** Verify the data structure:
```powershell
dir data\ljspeech_filtered\wavs
type data\ljspeech_filtered\metadata.csv | head
```

If empty, re-run:
```powershell
python scripts\format_data.py
```

---

### `espeak-ng` not found (Linux/macOS)

**Fix:**
```bash
# Ubuntu/Debian
sudo apt-get install espeak-ng

# macOS
brew install espeak-ng

# Verify Marathi support
espeak-ng --voices | grep " mr "
```

---

### Training loss not decreasing

- Verify your dataset has at least 100–200 valid samples (check `format_data.py` output)
- Try a larger `--batch-size` if GPU memory allows
- On Windows, try reducing `--learning-rate` (default in piper_train is fine for 250+ samples)
- On Linux, try fine-tuning from the English checkpoint instead of from scratch

---

### Audio sounds robotic / unintelligible

- The model needs more epochs — continue training
- Try `--length-scale 1.2` at inference time
- Check that `format_data.py` filtered out very short clips (< 1 s) and very long ones (> 15 s)
- Dataset quality matters more than quantity — ensure audio is clean and single-speaker

---

## 13. Training Tips

1. **Dataset quality > dataset size.** 250 clean, consistent recordings beat 1,000 noisy ones.

2. **Save checkpoints frequently.** The default is every 50 epochs. Use `--checkpoint-epochs 25` if disk space allows.

3. **Monitor validation loss, not just training loss.** Stop when val_loss plateaus or starts rising (overfitting).

4. **Test audio frequently.** Use `test_checkpoint.py` every 100 epochs. Ear-testing reveals quality gains faster than loss curves.

5. **Use length-scale at inference.** A value of 1.1–1.3 makes Marathi speech sound more natural without retraining.

6. **Fine-tuning is 3–5x faster than from scratch.** If you have access to Linux or Colab, use `train.sh` instead of `train.bat`.

7. **Google Drive persistence on Colab.** Mount Drive and set `--default_root_dir /content/drive/MyDrive/MarathiTTS/` to keep checkpoints between sessions.

---

*MarathiTTSv1 — Built with Piper TTS + VITS + OpenSLR-64*
