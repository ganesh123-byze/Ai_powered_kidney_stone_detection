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
        print(f"✓ Model copied to {MODEL_PATH}")
        return 0
    
    # Render deployment: download from GitHub
    print(f"📦 Downloading model from GitHub Releases...")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    if download_file(GITHUB_RELEASE_URL, MODEL_PATH):
        size_mb = MODEL_PATH.stat().st_size / 1024 / 1024
        print(f"✓ Model ready: {size_mb:.1f}MB")
        return 0
    
    # Try backup URL if primary fails
    if BACKUP_URL:
        print(f"\n⚠️  Primary URL failed, trying backup...")
        if download_file(BACKUP_URL, MODEL_PATH):
            return 0
    
    # Model download failed - provide helpful message
    print("\n" + "=" * 60)
    print("✗ MODEL DOWNLOAD FAILED")
    print("=" * 60)
    print("\nThe model file could not be downloaded from GitHub Releases.")
    print("This is EXPECTED if this is the first deployment.")
    print("\n📌 TO FIX THIS:")
    print("1. Upload your model to GitHub Releases:")
    print("   https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases")
    print("")
    print("2. Copy the download URL and update this script:")
    print("   GITHUB_RELEASE_URL = 'your-url-here'")
    print("")
    print("3. Re-deploy to Render or run this script again.")
    print("")
    print("⏳ For now, continuing without model...")
    print("   (API will work but predictions will fail until model is available)")
    print("=" * 60 + "\n")
    
    # Don't exit with error - allows server to start
    # API will fail gracefully when trying to predict without model
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
