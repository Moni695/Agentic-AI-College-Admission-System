@echo off
setlocal
cd /d "%~dp0.."
echo ===================================================
echo Pushing Agentic AI College Admission System to GitHub
echo Repository: https://github.com/Moni695/Agentic-AI-College-Admission-System
echo User:       Mohankumar HV (Moni695)
echo ===================================================

echo.
echo [1/4] Configuring Git author...
git config user.name "Mohankumar HV"
git config user.email "mohankumarhv199@gmail.com"

echo.
echo [2/4] Staging changes...
git add .

echo.
echo [3/4] Committing deployment setup...
git commit -m "Add production deployment configurations (Docker, Render, SQLite fallback, and runner scripts)"

echo.
echo [4/4] Pushing to GitHub (main branch)...
git push -u origin main

if %errorlevel% equ 0 (
  echo.
  echo ===================================================
  echo SUCCESS! Your project is now updated on GitHub:
  echo https://github.com/Moni695/Agentic-AI-College-Admission-System
  echo ===================================================
) else (
  echo.
  echo [NOTE] If you were prompted for a password, GitHub requires a
  echo Personal Access Token (PAT) instead of your account password.
)

echo.
pause
