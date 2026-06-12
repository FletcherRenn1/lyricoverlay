@echo off
echo === LyricOverlay Setup ===
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install Python 3.11+ from python.org
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: pip install failed. Try running as administrator.
    pause
    exit /b 1
)

echo.
echo === Setup complete! ===
echo.
echo Run the app with:  python main.py
echo.
echo First-time Spotify setup:
echo   1. Open Settings (gear icon)
echo   2. Go to the Spotify tab
echo   3. Follow the instructions to create a Spotify app
echo   4. Paste your Client ID and Secret, then click Connect
echo.
pause
