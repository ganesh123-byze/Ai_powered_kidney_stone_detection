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
# PRIORITY: Download .onnx (lightweight, no torch needed)
# FALLBACK: Use .pth (will convert to .onnx if torch available)
MODEL_FILENAME = "best_model.onnx"  # Changed from .pth for Render compatibility
MODEL_DIR = Path("saved_models")
MODEL_PATH = MODEL_DIR / MODEL_FILENAME

# Download URLs (try in order)
# Option 1: GitHub Releases - ONNX model (recommended for production)
GITHUB_RELEASE_URL = "https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases/download/v1.1.0/best_model.onnx"

# Option 2: Fallback to .pth if ONNX not available
GITHUB_RELEASE_URL_PTH = "https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases/download/v1.1.0/best_model.pth"

# Option 3: Direct URL or backup source (optional)
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
    """Main download logic with ONNX-first, PTH-fallback strategy."""
    print("=" * 60)
    print("🎯 Kidney Stone Detection - Model Downloader")
    print("=" * 60)
    
    model_dir = Path("saved_models")
    onnx_model = model_dir / "best_model.onnx"
    pth_model = model_dir / "best_model.pth"
    
    # Check if either model already exists
    if onnx_model.exists():
        size_mb = onnx_model.stat().st_size / 1024 / 1024
        print(f"✓ ONNX model present: {onnx_model} ({size_mb:.1f}MB) - Ready to serve!")
        return 0
    
    if pth_model.exists():
        size_mb = pth_model.stat().st_size / 1024 / 1024
        print(f"✓ PyTorch model present: {pth_model} ({size_mb:.1f}MB)")
        print("  Will convert to ONNX if PyTorch available, else will load as-is")
        return 0
    
    # For development: check local backup
    if LOCAL_MODEL_PATH.exists() and not os.getenv('RENDER'):
        print(f"ℹ Using local model: {LOCAL_MODEL_PATH}")
        model_dir.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy(LOCAL_MODEL_PATH, onnx_model if LOCAL_MODEL_PATH.suffix == '.onnx' else pth_model)
        print(f"✓ Model copied")
        return 0
    
    # Render deployment: Try downloading ONNX first (production-ready)
    print(f"📦 Strategy: ONNX (lightweight + no torch) → PTH (fallback)")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Try ONNX first
    print(f"\n[1/2] Attempting to download ONNX model...")
    if download_file(GITHUB_RELEASE_URL, onnx_model):
        size_mb = onnx_model.stat().st_size / 1024 / 1024
        print(f"✓ ONNX Model ready: {size_mb:.1f}MB - Optimal for Render!")
        return 0
    
    # Fallback to PTH
    print(f"\n[2/2] ONNX not available. Trying PyTorch model as fallback...")
    if download_file(GITHUB_RELEASE_URL_PTH, pth_model):
        size_mb = pth_model.stat().st_size / 1024 / 1024
        print(f"✓ PyTorch model ready: {size_mb:.1f}MB")
        print("  Note: Will auto-convert to ONNX if torch is available")
        return 0
    
    # Try backup URL if primary fails
    if BACKUP_URL:
        print(f"\n⚠️  Primary URLs failed, trying backup...")
        if download_file(BACKUP_URL, onnx_model) or download_file(BACKUP_URL.replace('.onnx', '.pth'), pth_model):
            return 0
    
    # Model download failed - provide helpful message
    print("\n" + "=" * 60)
    print("⚠️  MODEL DOWNLOAD FAILED")
    print("=" * 60)
    print("\nBoth ONNX and PyTorch models could not be downloaded.")
    print("This is EXPECTED if this is the first deployment.")
    print("\n📌 TO FIX THIS:")
    print("1. Convert your .pth to .onnx locally:")
    print("   pip install torch torchvision")
    print("   python -c 'from backend.app.models.model_loader import ModelLoader;")
    print("              m = ModelLoader(); m._convert_pth_to_onnx(\"best_model.pth\", \"best_model.onnx\")'")
    print("")
    print("2. Upload ONNX to GitHub Releases:")
    print("   https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases")
    print("")
    print("3. Update download URLs in this script")
    print("")
    print("⏳ Continuing without model... (API will start but predictions will fail)")
    print("=" * 60 + "\n")
    
    # Don't exit with error - allows server to start
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
