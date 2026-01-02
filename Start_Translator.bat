@echo off
TITLE AI Spanish -> Japanese Translator
echo ===================================================
echo      STARTING AI TRANSLATOR (ES - JP)...
echo ===================================================

:: 1. Check if Virtual Environment exists
if not exist "venv" (
    echo [!] Creating virtual environment...
    python -m venv venv
    echo [!] Installing dependencies...
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

:: 2. Check if Ollama is running (Crucial for the AI part)
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] Ollama is running.
) else (
    echo [!] WARNING: Ollama does not seem to be running!
    echo     Please open the Ollama app separately, otherwise the translation will fail.
)

echo.
echo Launching Interface...
python app_translator.py

pause