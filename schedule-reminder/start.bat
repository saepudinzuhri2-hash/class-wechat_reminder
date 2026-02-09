@echo off
cd /d "%~dp0"
echo.
echo ============================================
echo      Schedule Reminder - Startup
echo ============================================
echo.
echo Current Directory: %cd%
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    echo.
    echo Solution:
    echo 1. Visit https://www.python.org/downloads/
    echo 2. Download Python 3.8 or higher
    echo 3. Check "Add Python to PATH" during installation
    echo 4. Restart your computer
    echo.
    pause
    exit /b 1
)

echo [1/3] Python check... PASSED
python --version
echo.

REM Check virtual environment
if not exist venv (
    echo [2/3] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created
) else (
    echo [2/3] Virtual environment exists
)

echo.
echo [3/3] Installing dependencies...
echo This may take a few minutes...
venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies
    echo.
    echo Try manual installation:
    echo venv\Scripts\python -m pip install --upgrade pip
    echo venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo Dependencies installed!
echo.
echo ============================================
echo      Starting Schedule Reminder...
echo ============================================
echo.
echo Starting server, please wait...
echo Open browser: http://localhost:5000
echo.
echo Tip: Configure PushPlus Token in Settings page
echo.
echo Press Ctrl+C to stop
echo.

venv\Scripts\python app.py

echo.
echo ============================================
echo Server stopped
pause
