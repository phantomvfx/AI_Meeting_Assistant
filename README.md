# AI Meeting Assistant & Universal Translator

A local AI tool suite containing:
1.  **Meeting Assistant**: Transcribes meetings, finds mentions of keywords, and summarizes action items.
2.  **Universal Translator**: Translates audio/video to a target language text with DOCX export.

## Prerequisites

1.  **Python 3.10+** installed.
2.  **Ollama** installed and running (`ollama serve`).
    - Model used: `gemma3:4b` (Run `ollama pull gemma3:4b`)
3.  **FFmpeg** installed and added to system PATH.

## Installation

1.  Clone this repository:
    ```bash
    git clone https://github.com/phantomvfx/AI_Meeting_Assistant.git
    cd AI_Meeting_Assistant
    ```

2.  Run the Startup Script:
    - Double-click **`Start_App.bat`**.
    - This script will automatically:
        - Create a virtual environment (`venv`).
        - Install dependencies from `requirements.txt`.
        - Check if Ollama is running.
        - Launch the application.

## usage

- Open the web interface (usually `http://127.0.0.1:7860`).
- Select the tab for the tool you want to use.
