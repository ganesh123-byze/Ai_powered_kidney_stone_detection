@echo off
REM ============================================================================
REM Render Production Startup Script (Windows version for testing)
REM ============================================================================

echo.
echo ==========================================
echo Kidney Detection Backend - Startup Check
echo ==========================================
echo.

REM Check Python version
echo [1/5] Checking Python version...
python --version
if errorlevel 1 (
    echo. ERROR: Python not found!
    exit /b 1
)
echo OK
echo.

REM Verify PyTorch
echo [2/5] Verifying PyTorch...
python -c "import torch; print('PyTorch version:', torch.__version__)" 2>nul
if errorlevel 1 (
    echo WARNING: PyTorch not found, installing...
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
)
echo OK
echo.

REM Verify dependencies
echo [3/5] Verifying dependencies...
python -c "import fastapi, uvicorn, cv2, PIL" 2>nul
if errorlevel 1 (
    echo WARNING: Missing dependencies, reinstalling...
    pip install --no-cache-dir -r requirements.txt
)
echo OK
echo.

REM Check model
echo [4/5] Checking model file...
if not exist "saved_models\best_model.pth" (
    echo WARNING: Model not found, downloading...
    python download_model.py
    if errorlevel 1 (
        echo ERROR: Failed to download model!
        exit /b 1
    )
)
echo OK
echo.

REM Start server
echo [5/5] Starting Uvicorn server...
echo.
echo ==========================================
echo Starting server on http://0.0.0.0:8000
echo ==========================================
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
