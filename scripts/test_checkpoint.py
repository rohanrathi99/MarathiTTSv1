"""
Test a training checkpoint by generating sample audio.

Usage:
    python scripts/test_checkpoint.py <checkpoint_path> [--text "मराठी मजकूर"]
    python scripts/test_checkpoint.py training_filtered/lightning_logs/version_0/checkpoints/epoch=500-step=25000.ckpt
    python scripts/test_checkpoint.py <checkpoint_path> --text "नमस्कार, कसे आहात?"
    python scripts/test_checkpoint.py <checkpoint_path> --length-scale 1.2

Generates test audio in test_output/ directory.
"""
import os
import sys
import json
import argparse
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PIPER_PYTHON = os.path.join(PROJECT_ROOT, "piper_train", "src", "python")


def main():
    parser = argparse.ArgumentParser(description="Test a Piper training checkpoint")
    parser.add_argument("checkpoint", help="Path to .ckpt file")
    parser.add_argument("--text", default=None,
                        help="Text to synthesize (default: first line from dataset)")
    parser.add_argument("--output-dir", default=os.path.join(PROJECT_ROOT, "test_output"),
                        help="Output directory for test audio")
    parser.add_argument("--length-scale", type=float, default=1.1,
                        help="Speech speed (1.0=normal, 1.1-1.3=slower/more natural)")
    parser.add_argument("--sample-rate", type=int, default=22050,
                        help="Sample rate (must match training config)")
    args = parser.parse_args()

    if not os.path.exists(args.checkpoint):
        print(f"ERROR: Checkpoint not found: {args.checkpoint}")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    # Build the command
    env = {**os.environ, "PYTHONPATH": PIPER_PYTHON}

    if args.text:
        # Write text to a temp jsonl file (piper_train.infer reads from jsonl)
        import tempfile
        temp_jsonl = os.path.join(args.output_dir, "test_input.jsonl")
        with open(temp_jsonl, 'w', encoding='utf-8') as f:
            json.dump({"text": args.text}, f, ensure_ascii=False)
            f.write('\n')

        cmd = [
            sys.executable, "-m", "piper_train.infer",
            "--checkpoint", args.checkpoint,
            "--sample-rate", str(args.sample_rate),
            "--output-dir", args.output_dir,
            "--length-scale", str(args.length_scale),
        ]

        print(f"Generating speech for: {args.text}")
        print(f"Checkpoint: {args.checkpoint}")
        print(f"Output dir: {args.output_dir}")
        print(f"Length scale: {args.length_scale}")
        print()

        # Pipe the text via stdin
        result = subprocess.run(
            cmd, env=env,
            input=json.dumps({"text": args.text}, ensure_ascii=False) + '\n',
            capture_output=False, text=True
        )
    else:
        # Use first line from dataset.jsonl
        dataset_jsonl = os.path.join(PROJECT_ROOT, "training_filtered", "dataset.jsonl")
        if not os.path.exists(dataset_jsonl):
            print(f"ERROR: No dataset.jsonl found at {dataset_jsonl}")
            print("Either provide --text or run preprocessing first.")
            sys.exit(1)

        print(f"Using first line from: {dataset_jsonl}")
        print(f"Checkpoint: {args.checkpoint}")
        print(f"Output dir: {args.output_dir}")
        print()

        with open(dataset_jsonl, 'r', encoding='utf-8') as f:
            first_line = f.readline()

        cmd = [
            sys.executable, "-m", "piper_train.infer",
            "--checkpoint", args.checkpoint,
            "--sample-rate", str(args.sample_rate),
            "--output-dir", args.output_dir,
            "--length-scale", str(args.length_scale),
        ]

        result = subprocess.run(
            cmd, env=env,
            input=first_line,
            capture_output=False, text=True
        )

    if result.returncode == 0:
        print(f"\nTest audio saved to: {args.output_dir}/")
        # List generated files
        for f in sorted(os.listdir(args.output_dir)):
            if f.endswith('.wav'):
                fpath = os.path.join(args.output_dir, f)
                size_kb = os.path.getsize(fpath) / 1024
                print(f"  {f} ({size_kb:.1f} KB)")
    else:
        print(f"\nERROR: Inference failed (exit code {result.returncode})")
        sys.exit(1)


if __name__ == "__main__":
    main()
