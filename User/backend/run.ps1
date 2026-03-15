# Run Flask backend (port 5000). Use from project root or from backend/.
$ErrorActionPreference = "Stop"
$backendDir = $PSScriptRoot
Push-Location $backendDir
try {
    if (-not (Test-Path "venv\Scripts\python.exe")) {
        Write-Host "Creating venv..."
        python -m venv venv
    }
    Write-Host "Installing dependencies (if needed)..."
    & .\venv\Scripts\pip.exe install -q -r requirements.txt
    Write-Host "Starting backend at http://localhost:5000"
    & .\venv\Scripts\python.exe -m src.api.app
} finally {
    Pop-Location
}
