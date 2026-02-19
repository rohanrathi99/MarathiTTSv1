import os
import urllib.request
import zipfile
import sys

DATA_DIR = "data"
DATASET_URL = "https://www.openslr.org/resources/64/mr_in_female.zip"
LINE_INDEX_URL = "https://www.openslr.org/resources/64/line_index.tsv"
ZIP_FILE = os.path.join(DATA_DIR, "mr_in_female.zip")
EXTRACT_DIR = os.path.join(DATA_DIR, "mr_in_female")

def download_file(url, path):
    if os.path.exists(path):
        print(f"File already exists: {path}")
        return True
    
    print(f"Downloading {url} to {path}...")
    try:
        urllib.request.urlretrieve(url, path, reporthook=progress_hook)
        print("\nDownload complete.")
        return True
    except Exception as e:
        print(f"\nDownload failed: {e}")
        return False

def progress_hook(block_num, block_size, total_size):
    if total_size > 0:
        percent = int(block_num * block_size * 100 / total_size)
        sys.stdout.write(f"\rDownloading: {percent}%")
        sys.stdout.flush()

def extract_zip(zip_path, extract_to):
    print(f"Extracting {zip_path} to {extract_to}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print("Extraction complete.")

def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # Download Zip
    if download_file(DATASET_URL, ZIP_FILE):
        # Extract
        if not os.path.exists(EXTRACT_DIR):
             # The zip might contain a folder or just files. 
             # Based on README: "Place OpenSLR-64 files in data/mr_in_female/"
             # Let's extract to data/mr_in_female?
             # Usually openslr zips contain the files directly or a folder.
             # Let's verify content if possible, or just extract to mr_in_female
             os.makedirs(EXTRACT_DIR, exist_ok=True)
             extract_zip(ZIP_FILE, EXTRACT_DIR)
    
    # Download line_index.tsv
    download_file(LINE_INDEX_URL, os.path.join(DATA_DIR, "line_index.tsv"))

if __name__ == "__main__":
    main()
