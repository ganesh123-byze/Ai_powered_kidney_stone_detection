"""
Model Downloader for Render Deployment
Downloads the kidney stone detection model during the build process.
Supports downloading from GitHub Releases or direct URL.
"""

import os
import sys
from pathlib import Path
import urllib.request
import urllib.error

# Model configuration
MODEL_FILENAME = "best_model.pth"
MODEL_DIR = Path("saved_models")
MODEL_PATH = MODEL_DIR / MODEL_FILENAME

# Download URLs (try in order)
# Option 1: GitHub Releases (recommended - set your own URL)
GITHUB_RELEASE_URL = "https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases/download/v1.0.0/best_model.pth"

# Option 2: Direct URL or backup source (optional)
BACKUP_URL = None

# Local fallback (for development)
LOCAL_MODEL_PATH = Path("../backend/saved_models/best_model.pth")


def download_file(url, output_path, chunk_size=8192):
    """Download file from URL with progress reporting."""
    try:
        print(f"📥 Downloading from: {url}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with urllib.request.urlopen(url) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percentage = (downloaded / total_size) * 100
                        print(f"  Progress: {percentage:.1f}% ({downloaded / 1024 / 1024:.1f}MB / {total_size / 1024 / 1024:.1f}MB)")
        
        print(f"✓ Model downloaded successfully: {output_path}")
        return True
    
    except urllib.error.URLError as e:
        print(f"✗ Download failed: {e}")
        return False


def main():
    """Main download logic."""
    print("=" * 60)
    print("🎯 Kidney Stone Detection - Model Downloader")
    print("=" * 60)
    
    # Check if model already exists locally
    if MODEL_PATH.exists():
        size_mb = MODEL_PATH.stat().st_size / 1024 / 1024
        print(f"✓ Model already present: {MODEL_PATH} ({size_mb:.1f}MB)")
        return 0
    
    # For development: check local backup
    if LOCAL_MODEL_PATH.exists() and not os.getenv('RENDER'):
        print(f"ℹ Using local model: {LOCAL_MODEL_PATH}")
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy(LOCAL_MODEL_PATH, MODEL_PATH)
        return 0
    
    # Render deployment: download from GitHub
    if os.getenv('RENDER'):
        print(f"📦 Render environment detected - downloading model from GitHub...")
        
        if download_file(GITHUB_RELEASE_URL, MODEL_PATH):
            return 0
        # Try backup URL if primary fails
        elif BACKUP_URL and download_file(BACKUP_URL, MODEL_PATH):
            return 0
        else:
            print("\n⚠️  WARNING: Model download failed!")
            print("The model will need to be downloaded manually or provided via:")
            print("  1. Upload to GitHub Releases: https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases")
            print("  2. Use Render persistent disk")
            print("  3. Mount model from external storage")
            return 1
    
    print("✗ Model not found and download URLs not configured")
    print("\nTo set up model download:")
    print("  1. Upload model to: https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases/new")
    print("  2. Update GITHUB_RELEASE_URL in this script")
    print("  3. Re-deploy to Render")
    return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
