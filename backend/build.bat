@echo off
REM ============================================================================
REM Backend Build Script for Local Development
REM ============================================================================
REM Simulates Render build process locally

echo.
echo ================================
echo Building Kidney Detection Backend
echo ================================
echo.

REM Install Python dependencies
echo [1/3] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 goto error

REM Install PyTorch
echo.
echo [2/3] Installing PyTorch (CPU-only for local testing)...
pip install torch torchvision --index-url https://download.pytorch.org/whl/

if errorlevel 1 goto error

REM Download/verify model
echo.
echo [3/3] Checking/downloading model...
python download_model.py
if errorlevel 1 goto error

echo.
echo ================================
echo Build complete! ✅
echo ================================
echo.
echo Next: Run the backend with:
echo   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
echo.

goto end

:error
echo.
echo ❌ Build failed!
exit /b 1

:end
