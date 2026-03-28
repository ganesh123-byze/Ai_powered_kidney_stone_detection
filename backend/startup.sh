#!/bin/bash
# ============================================================================
# Render Production Startup Script
# ============================================================================
# This script ensures all dependencies are properly installed before starting
# the FastAPI server. It performs pre-flight checks and handles PyTorch setup.

set -e  # Exit on any error

echo "=========================================="
echo "🚀 Kidney Detection Backend - Startup"
echo "=========================================="

# Check Python version
echo "[1/5] Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION"

# Check if pip is available
echo "[2/5] Checking pip..."
if ! command -v pip &> /dev/null; then
    echo "✗ pip not found!"
    exit 1
fi
echo "✓ pip available"

# Verify torch is installed
echo "[3/5] Verifying PyTorch installation..."
if ! python -c "import torch; print(f'PyTorch version: {torch.__version__}')" 2>/dev/null; then
    echo "⚠️  PyTorch not found, installing..."
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
    if ! python -c "import torch" 2>/dev/null; then
        echo "✗ Failed to install PyTorch!"
        exit 1
    fi
fi
echo "✓ PyTorch verified"

# Verify other critical dependencies
echo "[4/5] Verifying dependencies..."
REQUIRED_MODULES="fastapi uvicorn pillow cv2 numpy loguru"
for module in $REQUIRED_MODULES; do
    if ! python -c "import $module" 2>/dev/null; then
        echo "⚠️  Missing module: $module, reinstalling dependencies..."
        pip install --no-cache-dir -r requirements.txt
        break
    fi
done
echo "✓ All dependencies verified"

# Check model file exists
echo "[5/5] Checking model file..."
if [ ! -f "saved_models/best_model.pth" ]; then
    echo "⚠️  Model file not found! Downloading..."
    if ! python download_model.py; then
        echo "✗ Failed to download model!"
        exit 1
    fi
fi
echo "✓ Model file verified"

echo ""
echo "=========================================="
echo "✅ All checks passed! Starting server..."
echo "=========================================="
echo ""

# Start the server with timeout and graceful shutdown
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --timeout-keep-alive 65 \
    --timeout-notify 30
