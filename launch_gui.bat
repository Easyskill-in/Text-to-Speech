@echo off
title AI Voice Generator
cd /d "%~dp0"

echo ============================================
echo    AI Voice Generator - First Time Setup
echo ============================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

if not exist "venv\Lib\site-packages\piper" (
    echo [2/4] Installing dependencies...
    pip install -r requirements.txt
) else (
    echo [2/4] Dependencies OK.
)

if not exist "models\en\en_US\lessac\medium\en_US-lessac-medium.onnx" (
    echo [3/4] Downloading voice models...
    python download_models.py
) else (
    echo [3/4] Voice models OK.
)

if not exist "output" mkdir output

echo.
echo [4/4] Starting AI Voice Generator...
python gui.py
pause
