# Start Kidney Detection Frontend
# Vite development server for React frontend

Write-Host "Starting Kidney Stone Detection Frontend..." -ForegroundColor Green
Write-Host ""

# Install dependencies if needed
Write-Host "Checking dependencies..." -ForegroundColor Cyan
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm packages..." -ForegroundColor Yellow
    npm install
}

Write-Host ""
Write-Host "Starting Vite dev server..." -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:5173 (or next available port)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Make sure the backend is running:" -ForegroundColor Yellow
Write-Host "  cd backend && ./run.ps1" -ForegroundColor Yellow
Write-Host ""

# Start frontend
npm run dev

Write-Host "Frontend stopped" -ForegroundColor Yellow
