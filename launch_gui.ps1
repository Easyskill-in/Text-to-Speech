# AI Voice Generator - Launcher
Write-Host "Starting AI Voice Generator..." -ForegroundColor Cyan
Set-Location $PSScriptRoot
& .\venv\Scripts\Activate.ps1
python gui.py
