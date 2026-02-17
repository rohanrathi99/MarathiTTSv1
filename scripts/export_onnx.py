"""
Export trained Piper checkpoint to ONNX format for Raspberry Pi deployment.

Usage:
    python scripts/export_onnx.py <checkpoint_path> [output_path]

Example:
    python scripts/export_onnx.py training_filtered/lightning_logs/version_0/checkpoints/epoch=999-step=50000.ckpt
    python scripts/export_onnx.py training_filtered/lightning_logs/version_0/checkpoints/epoch=999-step=50000.ckpt output/marathi-medium.onnx
"""
import os
import sys
import shutil
import argparse

# Setup path for piper_train imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PIPER_PYTHON = os.path.join(PROJECT_ROOT, "piper_train", "src", "python")
sys.path.insert(0, PIPER_PYTHON)
os.environ.setdefault("PYTHONPATH", PIPER_PYTHON)


def main():
    parser = argparse.ArgumentParser(description="Export Piper checkpoint to ONNX")
    parser.add_argument("checkpoint", help="Path to .ckpt file")
    parser.add_argument("output", nargs="?", default=None,
                        help="Output .onnx path (default: output/marathi-medium.onnx)")
    args = parser.parse_args()

    if not os.path.exists(args.checkpoint):
        print(f"ERROR: Checkpoint not found: {args.checkpoint}")
        sys.exit(1)

    # Default output path
    if args.output is None:
        output_dir = os.path.join(PROJECT_ROOT, "output")
        os.makedirs(output_dir, exist_ok=True)
        args.output = os.path.join(output_dir, "marathi-medium.onnx")

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print(f"Exporting checkpoint to ONNX...")
    print(f"  Checkpoint: {args.checkpoint}")
    print(f"  Output:     {args.output}")

    # Run piper_train.export_onnx
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "piper_train.export_onnx", args.checkpoint, args.output],
        env={**os.environ, "PYTHONPATH": PIPER_PYTHON},
        capture_output=False
    )

    if result.returncode != 0:
        print("ERROR: Export failed.")
        sys.exit(1)

    # Copy config.json alongside the ONNX file
    training_dir = os.path.join(PROJECT_ROOT, "training_filtered")
    config_src = os.path.join(training_dir, "config.json")
    config_dst = args.output + ".json"

    if os.path.exists(config_src):
        shutil.copy2(config_src, config_dst)
        print(f"  Config:     {config_dst}")
    else:
        print(f"  WARNING: config.json not found at {config_src}")
        print(f"  You'll need to copy it manually for Piper to work.")

    print()
    print("=== Export Complete ===")
    print(f"Deploy these two files to your Raspberry Pi:")
    print(f"  1. {args.output}")
    print(f"  2. {config_dst}")
    print()
    print("Test with:")
    print(f'  echo "नमस्कार" | piper --model {os.path.basename(args.output)} --output_file test.wav')


if __name__ == "__main__":
    main()
