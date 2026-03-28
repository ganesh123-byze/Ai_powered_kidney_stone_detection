#!/bin/bash
# ============================================================================
# Backend Build Script for Render
# ============================================================================
# This script is used as the build command on Render
# It installs dependencies, PyTorch, and downloads the model

set -e  # Exit on error

echo "================================"
echo "🔨 Building Kidney Detection Backend"
echo "================================"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install PyTorch (CPU optimized for Render)
echo "🔥 Installing PyTorch..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Download model
echo "📥 Downloading model..."
python download_model.py

echo "================================"
echo "✅ Build complete!"
echo "================================"
