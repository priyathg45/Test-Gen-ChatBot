# Run React frontend (port 3000). Use from project root or from frontend/.
$ErrorActionPreference = "Stop"
$frontendDir = $PSScriptRoot
Push-Location $frontendDir
try {
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing npm dependencies..."
        npm install
    }
    Write-Host "Starting frontend at http://localhost:3000"
    npm run dev
} finally {
    Pop-Location
}
