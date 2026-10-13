@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating local virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Could not create virtual environment. Install Python 3.11 or 3.12 and try again.
    pause
    exit /b 1
  )
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
".venv\Scripts\python.exe" -m streamlit run app.py
pause
