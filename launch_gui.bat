@echo off
title AI Voice Generator
cd /d "%~dp0"

echo ============================================
echo    AI Voice Generator - First Time Setup
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
    echo [1/4] Creating virtual environment...
    py -3.11 -m venv venv
)

call venv\Scripts\activate.bat

if not exist "venv\Lib\site-packages\kokoro" (
    echo [2/4] Installing dependencies...
    pip install -r requirements.txt
) else (
    echo [2/4] Dependencies OK.
)

if not exist "output" mkdir output

echo.
echo [4/4] Starting AI Voice Generator...
python gui.py
pause
