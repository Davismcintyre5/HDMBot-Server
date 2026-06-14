@echo off
title HDM BOT - Admin CLI

REM Go to server directory
cd /d "%~dp0.."

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo [ERROR] Failed to activate venv.
    pause
    exit /b 1
)

REM Run admin CLI
echo Starting Admin CLI...
python scripts/admin.py

REM Keep window open if error
pause