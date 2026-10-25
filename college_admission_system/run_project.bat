@echo off
setlocal
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  py -3.12 -m venv .venv
  call .venv\Scripts\activate
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate
)
if not exist ".env" copy .env.example .env
echo.
echo Configure backend\.env with your MySQL password before the first run.
echo Starting at http://127.0.0.1:8000
python -m uvicorn app.main:app --reload
endlocal
