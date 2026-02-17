# AiAntargyanV2 - Marathi TTS

A Marathi Text-to-Speech (TTS) training project using [Piper](https://github.com/rhasspy/piper) and the VITS architecture. This project uses the OpenSLR-64 Marathi dataset.

## Project Structure

- `data/`: Contains raw audio and transcripts (OpenSLR-64).
- `scripts/`: Helper scripts for data formatting and training.
- `piper_train/`: Modified Piper training scripts (patched for Windows & PyTorch Lightning 2.x).
- `training/`: Output directory for checkpoints, logs, and processed dataset.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install torch pytorch-lightning torchmetrics
    ```

2.  **Prepare Data**:
    The dataset is expected in `data/`. Run the formatting script:
    ```bash
    python scripts/format_data.py
    ```

3.  **Preprocessing**:
    Preprocessing generates the `dataset.jsonl` and `config.json` used for training.
    ```bash
    # This is handled automatically, or you can run:
    python -m piper_train.preprocess ...
    ```

## Training

To start training, simply run the provided batch script:
```batch
scripts\train.bat
```

This script will:
- set up the `PYTHONPATH` correctly.
- Auto-detect GPU/CPU (`--accelerator auto`).
- Start training with VITS.

## Notes

- **Windows Compatibility**: The `piper_train` code has been patched to skip `piper-phonemize` (which is hard to build on Windows) and use character-level input (`--phoneme-type text`) instead. This works well for Devanagari script.
- **PyTorch Lightning**: The code is patched to support newer PL versions (2.x).
