@echo off
setlocal
cd /d "%~dp0"
echo ===================================================
echo Starting Agentic AI College Admission System
echo ===================================================
echo Checking Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
  echo.
  echo [ERROR] Docker is not running!
  echo Please open Docker Desktop first, wait until it starts, and run this file again.
  echo.
  pause
  exit /b 1
)

echo.
echo Building and launching containers in background...
docker compose up -d --build

if %errorlevel% equ 0 (
  echo.
  echo ===================================================
  echo Successfully deployed!
  echo Web App:      http://localhost:8000
  echo API Docs:     http://localhost:8000/docs
  echo Admin Email:  admin@bcu-demo.edu
  echo Admin Pass:   Admin@123
  echo ===================================================
  echo.
  echo Opening browser...
  start http://localhost:8000
) else (
  echo.
  echo [ERROR] Docker Compose failed to start.
)

pause
