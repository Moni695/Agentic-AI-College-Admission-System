@echo off
setlocal
cd /d "%~dp0college_admission_system\backend"
echo ===================================================
echo Starting Bangalore University Admission System
echo ===================================================

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  py -3.12 -m venv .venv 2>nul || python -m venv .venv 2>nul || py -m venv .venv
  call .venv\Scripts\activate
  echo Installing dependencies (this may take a minute on first run)...
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate
)

if not exist ".env" copy .env.example .env

echo.
echo Application URL: http://localhost:8000
echo Admin Email:     admin@bcu-demo.edu
echo Admin Password:  Admin@123
echo.
echo Launching server... (Press Ctrl+C to stop)
start http://localhost:8000
python run.py
endlocal
