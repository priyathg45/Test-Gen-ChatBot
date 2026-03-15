@echo off
REM Run Ollama from default Windows path if not in PATH.
set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
where ollama >nul 2>&1
if %ERRORLEVEL% equ 0 (
  ollama %*
  exit /b %ERRORLEVEL%
)
if exist "%OLLAMA_EXE%" (
  "%OLLAMA_EXE%" %*
  exit /b %ERRORLEVEL%
)
echo Ollama not found.
echo 1. Download: https://ollama.com/download/windows
echo 2. Run OllamaSetup.exe and install.
echo 3. Close and reopen the terminal, then: ollama run llama3.2
echo.
echo To run without Ollama, set in .env: USE_OLLAMA_FOR_DOCUMENTS=false
exit /b 1
