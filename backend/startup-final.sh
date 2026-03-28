#!/bin/bash
# ============================================================================
# Production Startup Wrapper for Render
# ============================================================================
# This wrapper ensures PyTorch is installed before starting Uvicorn.
# It handles the case where installation might not be complete.

set -e

echo "=========================================="
echo "🚀 Kidney Detection Backend - Final Check"
echo "=========================================="
echo ""

# Check Python
echo "[1/3] Verifying Python..."
python --version

# Ensure torch is available (critical check)
echo "[2/3] Final PyTorch verification..."
if ! python -c "import torch; print(f'✓ PyTorch {torch.__version__}')" 2>/dev/null; then
    echo "⚠️  PyTorch missing! Installing now..."
    python -m pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
    
    # Verify installation succeeded
    if ! python -c "import torch" 2>/dev/null; then
        echo "✗ CRITICAL: PyTorch installation failed!"
        echo "  The server will start but predictions will fail."
        echo "  This is a build issue - contact support."
    fi
fi

# Verify model exists
echo "[3/3] Checking model file..."
if [ ! -f "saved_models/best_model.pth" ]; then
    echo "⚠️  Model not found. Attempting download..."
    python download_model.py || echo "  (Model will be downloaded on first request)"
fi

echo ""
echo "=========================================="
echo "✅ Startup check complete!"
echo "Starting Uvicorn server..."
echo "=========================================="
echo ""

# Start server
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --timeout-keep-alive 65 \
    --interface asgi3
