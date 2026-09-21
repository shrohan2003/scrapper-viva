@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Create the virtual environment and install requirements first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" capture.py
echo.
pause