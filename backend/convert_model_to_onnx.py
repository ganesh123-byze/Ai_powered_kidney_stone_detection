#!/usr/bin/env python3
"""
Convert PyTorch .pth model to ONNX format
Run this locally before uploading to GitHub releases
Usage: python backend/convert_model_to_onnx.py
"""

import os
import sys
from pathlib import Path

def convert_to_onnx():
    """Convert .pth model to .onnx format locally."""
    
    pth_path = Path("backend/saved_models/best_model.pth")
    onnx_path = Path("backend/saved_models/best_model.onnx")
    
    if not pth_path.exists():
        print(f"❌ Model not found: {pth_path}")
        sys.exit(1)
    
    if onnx_path.exists():
        print(f"⚠️  ONNX model already exists: {onnx_path}")
        response = input("Overwrite? (y/n): ").lower()
        if response != 'y':
            print("Cancelled.")
            sys.exit(0)
    
    print("=" * 60)
    print("🔄 Converting PyTorch Model to ONNX")
    print("=" * 60)
    print(f"Input:  {pth_path}")
    print(f"Output: {onnx_path}")
    print()
    
    # Check PyTorch availability
    try:
        import torch
        import torchvision.models as models
        print(f"✓ PyTorch {torch.__version__} available")
    except ImportError:
        print("❌ PyTorch not installed!")
        print("\nInstall with: pip install torch torchvision")
        sys.exit(1)
    
    try:
        from app.models.model_loader import ModelLoader
        
        loader = ModelLoader()
        loader._convert_pth_to_onnx(str(pth_path), str(onnx_path))
        
        size_mb = onnx_path.stat().st_size / 1024 / 1024
        print(f"\n✅ Conversion successful!")
        print(f"   File: {onnx_path}")
        print(f"   Size: {size_mb:.1f}MB")
        print(f"\n📤 Next steps:")
        print(f"   1. Upload ONNX to GitHub releases")
        print(f"   2. Update download URL in backend/download_model.py")
        print(f"   3. Re-deploy to Render")
        
    except Exception as e:
        print(f"\n❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Change to repo root
    os.chdir(Path(__file__).parent.parent)
    convert_to_onnx()
