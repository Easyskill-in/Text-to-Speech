@echo off
title Text to Video AI
cd /d "%~dp0"

echo ============================================
echo    Text to Video AI - First Time Setup
echo ============================================
echo.

py -3.11 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.11 is not installed!
    echo Please install Python 3.11 from https://python.org
    pause
    exit /b 1
)

if not exist "venv" (
    echo [1/3] Creating virtual environment...
    py -3.11 -m venv venv
)

call venv\Scripts\activate.bat

if not exist "venv\Lib\site-packages\kokoro" (
    echo [2/3] Installing dependencies...
    pip install -r requirements.txt
    pip install moviepy pillow
) else (
    echo [2/3] Dependencies OK.
)

if not exist "output" mkdir output

echo.
echo [3/3] Starting Text to Video AI...
python video_gui.py
pause
