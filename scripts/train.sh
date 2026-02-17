#!/bin/bash
# AiAntargyanV2 — Marathi TTS Training Script (Linux/Colab/Docker)
#
# Usage:
#   ./scripts/train.sh                    # Fine-tune from English checkpoint
#   ./scripts/train.sh --from-scratch     # Train from scratch (no checkpoint)
#   ./scripts/train.sh --batch-size 16    # Override batch size (for smaller GPUs)

set -e
cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"

export PYTHONPATH="$PROJECT_ROOT/piper_train/src/python"
DATASET_DIR="$PROJECT_ROOT/training_filtered"
CHECKPOINT="$PROJECT_ROOT/checkpoints/en_US-lessac-medium.ckpt"

# Parse arguments
FROM_SCRATCH=false
EXTRA_ARGS=()
for arg in "$@"; do
    if [ "$arg" = "--from-scratch" ]; then
        FROM_SCRATCH=true
    else
        EXTRA_ARGS+=("$arg")
    fi
done

# === 1. Preprocessing ===
echo "============================================"
echo "  AiAntargyanV2 — Marathi TTS Training"
echo "============================================"
echo ""

if [ ! -d "$PROJECT_ROOT/data/ljspeech_filtered/wavs" ]; then
    echo "ERROR: Dataset not found at data/ljspeech_filtered/"
    echo "Run 'python scripts/format_data.py' first."
    exit 1
fi

echo "[Step 1/2] Preprocessing dataset..."
python3 -m piper_train.preprocess \
    --language mr \
    --input-dir "$PROJECT_ROOT/data/ljspeech_filtered" \
    --output-dir "$DATASET_DIR" \
    --dataset-format ljspeech \
    --single-speaker \
    --sample-rate 22050

echo ""

# === 2. Training ===
echo "[Step 2/2] Starting training..."
echo "  Dataset:    $DATASET_DIR"
echo "  PYTHONPATH: $PYTHONPATH"

TRAIN_CMD=(
    python3 -m piper_train
    --dataset-dir "$DATASET_DIR"
    --accelerator auto
    --devices 1
    --batch-size 32
    --validation-split 0.05
    --num-test-examples 5
    --checkpoint-epochs 50
    --precision 32
)

if [ "$FROM_SCRATCH" = true ]; then
    echo "  Mode:       Training from scratch"
    TRAIN_CMD+=(--max_epochs 2000)
else
    if [ ! -f "$CHECKPOINT" ]; then
        echo "ERROR: Checkpoint not found at $CHECKPOINT"
        echo "Run 'python scripts/download_checkpoint.py' first,"
        echo "or use --from-scratch to train without a checkpoint."
        exit 1
    fi
    echo "  Mode:       Fine-tuning from $CHECKPOINT"
    TRAIN_CMD+=(
        --max_epochs 1000
        --resume_from_checkpoint "$CHECKPOINT"
    )
fi

echo ""

# Append any extra user arguments
"${TRAIN_CMD[@]}" "${EXTRA_ARGS[@]}"

echo ""
echo "Training complete!"
echo "Checkpoints are in: $DATASET_DIR/lightning_logs/"
