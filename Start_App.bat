@echo off
TITLE AI Meeting Assistant
echo ===================================================
echo      STARTING AI MEETING ASSISTANT...
echo ===================================================

if not exist "venv" (
    echo [!] Creating virtual environment...
    python -m venv venv
    echo [!] Installing dependencies...
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

echo.
echo Launching Interface...
python app_gui.py
pause