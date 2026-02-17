import os
import urllib.request
import hashlib

CHECKPOINT_URL = "https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/en/en_US/lessac/medium/epoch%3D2164-step%3D1355540.ckpt"
CHECKPOINT_PATH = r"d:\WorkStation\PlayGrounds\PlayGround-8\AiAntargyanV2\checkpoints\en_US-lessac-medium.ckpt"

def download_file(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        print(f"File already exists: {path}")
        return True
    
    print(f"Downloading {url} to {path}...")
    try:
        urllib.request.urlretrieve(url, path)
        print("Download complete.")
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

if __name__ == "__main__":
    download_file(CHECKPOINT_URL, CHECKPOINT_PATH)
