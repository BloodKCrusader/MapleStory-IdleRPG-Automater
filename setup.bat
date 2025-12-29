@echo off
echo ================================================
echo   MapleStory Idle Bot - Setup
echo ================================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python found!
echo.

REM Create virtual environment (optional but recommended)
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Warning: Could not create virtual environment
    echo Installing to system Python...
) else (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo.
echo Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo ================================================
echo   Setup Complete!
echo ================================================
echo.
echo Next steps:
echo   1. Configure BlueStacks (960x540, 240 DPI, ADB enabled)
echo   2. Run: python main.py
echo.
pause

