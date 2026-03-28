# Start Kidney Detection Backend
# Ensures uvicorn binds to correct host/port for frontend access

Write-Host "Starting Kidney Stone Detection Backend..." -ForegroundColor Green
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
$env:HOST = "0.0.0.0"
$env:PORT = "8000"
$env:DEBUG = "true"

# Start uvicorn with proper binding
uvicorn app.main:app `
    --host 0.0.0.0 `
    --port 8000 `
    --reload `
    --reload-dir=app

Write-Host "Backend stopped" -ForegroundColor Yellow
