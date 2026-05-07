"""
Falcone AI — One-Time Setup
Unzips the pre-built Qdrant database and verifies the collection.
"""

import zipfile
import os
import sys
from pathlib import Path

QDRANT_ZIP = "qdrant_db.zip"
QDRANT_DIR = "qdrant_db"
REQUIRED_DIRS = ["collection", "wal"]  # minimal Qdrant structure


def setup():
    # 1. Check if already extracted
    if Path(QDRANT_DIR).exists() and any(Path(QDRANT_DIR).iterdir()):
        print(f"[✓] '{QDRANT_DIR}' already exists and is not empty. Skipping extraction.")
        verify()
        return

    # 2. Check if zip exists
    if not Path(QDRANT_ZIP).exists():
        print(f"[✗] '{QDRANT_ZIP}' not found!")
        print("Make sure qdrant_db.zip is in the project root.")
        sys.exit(1)

    # 3. Extract
    print(f"[*] Extracting '{QDRANT_ZIP}'...")
    with zipfile.ZipFile(QDRANT_ZIP, "r") as zf:
        zf.extractall(".")
    print(f"[✓] Extracted to '{QDRANT_DIR}/'")

    # 4. Verify
    verify()


def verify():
    """Quick check that Qdrant directory has the expected structure."""
    qdrant_path = Path(QDRANT_DIR)
    
    if not qdrant_path.exists():
        print(f"[✗] '{QDRANT_DIR}' directory not found!")
        sys.exit(1)

    # Check essential subdirectories
    missing = [d for d in REQUIRED_DIRS if not (qdrant_path / d).exists()]
    if missing:
        print(f"[✗] Missing directories: {missing}")
        print("The database may be corrupted. Try re-extracting qdrant_db.zip.")
        sys.exit(1)

    # Check collection exists
    collection_dir = qdrant_path / "collection"
    if collection_dir.exists():
        collections = [d.name for d in collection_dir.iterdir() if d.is_dir()]
        if collections:
            print(f"[✓] Found collections: {collections}")
        else:
            print("[✗] No collections found. Database may be empty.")
            sys.exit(1)

    print("[✓] Qdrant database verified successfully!")
    print("[✓] Setup complete. You can now run: streamlit run app.py")


if __name__ == "__main__":
    setup()