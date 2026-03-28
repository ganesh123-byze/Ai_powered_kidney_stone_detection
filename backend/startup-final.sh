#!/bin/bash
# ============================================================================
# Production Startup Wrapper for Render (ONNX Runtime - CPU-only)
# ============================================================================
# This wrapper ensures ONNX Runtime is working before starting Uvicorn.
# No PyTorch installation needed - uses lightweightONNX Runtime instead.

set -e

echo "=========================================="
echo "🚀 Kidney Detection Backend - Final Check"
echo "=========================================="
echo ""

# Check Python
echo "[1/2] Verifying Python..."
python --version

# Verify ONNX Runtime is available
echo "[2/2] Verifying ONNX Runtime..."
if ! python -c "import onnxruntime; print(f'✓ ONNX Runtime {onnxruntime.__version__}')" 2>/dev/null; then
    echo "❌ CRITICAL: ONNX Runtime installation failed!"
    echo "  Please check build logs."
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Startup check complete!"
echo "Starting Uvicorn server..."
echo "=========================================="
echo ""

# Start server (CPU-only, lightweight)
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --timeout-keep-alive 65 \
    --interface asgi3
