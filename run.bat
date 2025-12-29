@echo off
echo Starting MapleStory Idle Bot...

REM Check if virtual environment exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

python main.py %*

if errorlevel 1 (
    echo.
    echo Bot exited with an error.
    pause
)

