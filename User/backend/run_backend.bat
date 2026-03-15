@echo off
cd /d "%~dp0"
if not exist "venv" (
  echo Creating venv...
  python -m venv venv
)
call venv\Scripts\activate.bat
if not exist "venv\Scripts\pip.exe" (
  echo Installing dependencies...
  pip install -r requirements.txt
)
echo Starting Flask API on http://localhost:5000
python -m src.api.app
