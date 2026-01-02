@echo off
TITLE AI AV Tools Suite
echo ===================================================
echo      STARTING AI AV TOOLS SUITE...
echo ===================================================

if not exist "venv" (
    echo [!] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] Ollama is running.
) else (
    echo [!] WARNING: Ollama is NOT running. Please open it!
)

echo.
echo Launching Unified Interface...
python app_unified.py
pause