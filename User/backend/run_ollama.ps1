# Run Ollama from default Windows install path if it's not in PATH.
# Usage: .\run_ollama.ps1 [run llama3.2]
$ollamaExe = $env:LOCALAPPDATA + "\Programs\Ollama\ollama.exe"
if (Get-Command ollama -ErrorAction SilentlyContinue) {
    & ollama @args
    exit $LASTEXITCODE
}
if (Test-Path $ollamaExe) {
    & $ollamaExe @args
    exit $LASTEXITCODE
}
Write-Host "Ollama not found." -ForegroundColor Yellow
Write-Host "1. Download the installer: https://ollama.com/download/windows"
Write-Host "2. Run OllamaSetup.exe and complete installation."
Write-Host "3. Close and reopen this terminal, then run: ollama run llama3.2"
Write-Host ""
Write-Host "To run the chatbot without Ollama, set in .env: USE_OLLAMA_FOR_DOCUMENTS=false"
exit 1
