"""
Download pre-trained checkpoint for fine-tuning.

FIXED: Uses relative paths (no hardcoded Windows paths)
ADDED: Download progress bar
"""
import os
import sys
import urllib.request

CHECKPOINT_URL = (
    "https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/"
    "en/en_US/lessac/medium/epoch%3D2164-step%3D1355540.ckpt"
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CHECKPOINT_PATH = os.path.join(PROJECT_ROOT, "checkpoints", "en_US-lessac-medium.ckpt")


class DownloadProgress:
    """Show download progress."""
    def __init__(self):
        self.last_percent = -1

    def __call__(self, block_num, block_size, total_size):
        if total_size > 0:
            percent = int(block_num * block_size * 100 / total_size)
            percent = min(percent, 100)
            if percent != self.last_percent:
                mb_done = (block_num * block_size) / (1024 * 1024)
                mb_total = total_size / (1024 * 1024)
                sys.stdout.write(f"\r  Downloading: {percent}% ({mb_done:.1f}/{mb_total:.1f} MB)")
                sys.stdout.flush()
                self.last_percent = percent


def download_file(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if os.path.exists(path):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"Checkpoint already exists: {path} ({size_mb:.1f} MB)")
        return True

    print(f"Downloading checkpoint...")
    print(f"  URL:  {url}")
    print(f"  Dest: {path}")

    try:
        urllib.request.urlretrieve(url, path, reporthook=DownloadProgress())
        print("\n  Download complete!")
        return True
    except Exception as e:
        print(f"\n  Download failed: {e}")
        # Clean up partial download
        if os.path.exists(path):
            os.remove(path)
        return False


if __name__ == "__main__":
    success = download_file(CHECKPOINT_URL, CHECKPOINT_PATH)
    if not success:
        sys.exit(1)
