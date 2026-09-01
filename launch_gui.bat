@echo off
title AI Voice Generator
cd /d "%~dp0"

echo ============================================
echo    AI Voice Generator - First Time Setup
echo ============================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://python.org
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

:: Create virtual environment if not exists
if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
)

:: Activate venv
call venv\Scripts\activate.bat

:: Install dependencies if not exists
if not exist "venv\Lib\site-packages\piper" (
    echo [2/4] Installing dependencies (first time only)...
    pip install -r requirements.txt
) else (
    echo [2/4] Dependencies already installed.
)

:: Download models if not exists
if not exist "models\en\en_US\lessac\medium\en_US-lessac-medium.onnx" (
    echo [3/4] Downloading voice models (first time only)...
    python download_models.py
) else (
    echo [3/4] Voice models already downloaded.
)

:: Create output folder
if not exist "output" mkdir output

echo [4/4] Starting AI Voice Generator...
echo.
python gui.py
pause
