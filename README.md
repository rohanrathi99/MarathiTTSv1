# AiAntargyanV2 - Marathi TTS

A Marathi Text-to-Speech (TTS) training project using [Piper](https://github.com/rhasspy/piper) and the VITS architecture. This project uses the OpenSLR-64 Marathi dataset.

## Project Structure

- `data/`: Contains raw audio `mr_in_female` and filtered dataset `ljspeech_filtered`.
- `scripts/`: Helper scripts for data formatting, normalization, and training.
- `piper_train/`: Modified Piper training scripts (patched for Windows & PyTorch Lightning 2.x).
- `training_filtered/`: Output directory for checkpoints, logs, and processed dataset (from filtered data).
- `checkpoints/`: Contains pre-trained checkpoints for fine-tuning.

## Guide Aligned Setup

This project follows a "Guide Aligned" approach for higher quality:
1.  **Best Speaker Selection**: Automatically filters for speaker `04310` (most frequent).
2.  **Audio Filtering**: Removes clips based on duration (1-15s) and RMS amplitude.
3.  **Robust Normalization**: Uses detailed Marathi text normalization.
4.  **Fine-Tuning**: Uses an English checkpoint to bootstrap training.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install torch pytorch-lightning torchmetrics
    ```

2.  **Prepare Data**:
    Run the formatting script to generate the filtered and normalized dataset in `data/ljspeech_filtered`:
    ```bash
    python scripts/format_data.py
    ```

3.  **Download Checkpoint**:
    Download the pre-trained English checkpoint for fine-tuning:
    ```bash
    python scripts/download_checkpoint.py
    ```

## Training

To start training (Fine-Tuning mode), run:
```batch
scripts\train.bat
```

This script will:
- Run preprocessing on `data/ljspeech_filtered` if needed.
- Start VITS training using the `en_US-lessac-medium.ckpt` checkpoint.
- Auto-detect GPU/CPU.

## Notes

- **Windows Compatibility**: The `piper_train` code has been patched to skip `piper-phonemize` (which is hard to build on Windows) and use character-level input (`--phoneme-type text`) instead. This works well for Devanagari script.
- **PyTorch Lightning**: The code is patched to support newer PL versions (2.x).
