#!/bin/bash
# Setup Piper TTS training code for AiAntargyanV2
#
# This script clones the Piper repository and sets it up for training.
# Run this once before training.
#
# Usage:
#   ./scripts/setup_piper.sh
#
# For Windows users: see setup_piper.bat or follow manual steps in README.

set -e
cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"

echo "============================================"
echo "  Setting up Piper TTS Training Code"
echo "============================================"
echo ""

# 1. Clone Piper
if [ -d "piper_train" ]; then
    echo "piper_train/ already exists. Skipping clone."
    echo "To re-clone, delete the directory first: rm -rf piper_train"
else
    echo "[Step 1/4] Cloning Piper repository..."
    git clone https://github.com/rhasspy/piper.git piper_train_temp
    # We only need the Python training code
    mkdir -p piper_train
    cp -r piper_train_temp/src piper_train/
    rm -rf piper_train_temp
    echo "  Done."
fi

echo ""

# 2. Install system dependencies
echo "[Step 2/4] Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq espeak-ng libespeak-ng1 libsndfile1 ffmpeg
elif command -v yum &> /dev/null; then
    sudo yum install -y espeak-ng libsndfile ffmpeg
elif command -v brew &> /dev/null; then
    brew install espeak-ng libsndfile ffmpeg
else
    echo "  WARNING: Could not detect package manager."
    echo "  Please install manually: espeak-ng, libsndfile, ffmpeg"
fi
echo "  Done."

echo ""

# 3. Install Python dependencies
echo "[Step 3/4] Installing Python dependencies..."
pip install -r requirements.txt
pip install torch torchaudio --extra-index-url https://download.pytorch.org/whl/cu118

# Install piper training module
cd piper_train/src/python
pip install -e .
cd "$PROJECT_ROOT"
echo "  Done."

echo ""

# 4. Build Monotonic Alignment Search
echo "[Step 4/4] Building Monotonic Alignment Search extension..."
cd piper_train/src/python/piper_train/vits/monotonic_align
python setup.py build_ext --inplace
cd "$PROJECT_ROOT"
echo "  Done."

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Place OpenSLR-64 data in:  data/mr_in_female/"
echo "  2. Place line_index.tsv in:   data/line_index.tsv"
echo "  3. Run data preparation:      python scripts/format_data.py"
echo "  4. Download checkpoint:        python scripts/download_checkpoint.py"
echo "  5. Start training:            ./scripts/train.sh"
echo ""

# Verify espeak-ng Marathi support
echo "Verifying espeak-ng Marathi support..."
if command -v espeak-ng &> /dev/null; then
    if espeak-ng --voices | grep -q "mr"; then
        echo "  ✓ espeak-ng supports Marathi (mr)"
    else
        echo "  ✗ espeak-ng does NOT list Marathi."
        echo "    You may need to build espeak-ng from source for Marathi support."
        echo "    See: https://github.com/espeak-ng/espeak-ng"
    fi
else
    echo "  ✗ espeak-ng not found in PATH"
fi
