AI Meeting Assistant

A local, offline application for processing audiovisual meeting recordings. This tool utilizes OpenAI Whisper for transcription, OpenCV for frame extraction, and Ollama (LLM) for semantic analysis and summarization. It generates distinct HTML (Dark Mode) and PDF (Light Mode) reports containing executive summaries, action items, and timestamped visual references based on keyword detection.

Prerequisites

Ensure the following system dependencies are installed before running the application:

Python 3.10+

FFmpeg

Required by the Whisper library for audio processing.

Windows: winget install ffmpeg (or add to PATH manually).

Mac: brew install ffmpeg.

Ollama

Required for local LLM inference.

Download from ollama.com.

Model Setup: You must pull the model specified in the code (default is gemma3:4b). Run the following command in your terminal:

code
Bash
download
content_copy
expand_less
ollama run gemma3:4b
Installation

Clone the repository:

code
Bash
download
content_copy
expand_less
git clone https://github.com/phantomvfx/AI_Meeting_Assistant.git
cd AI_Meeting_Assistant

Create a Virtual Environment:

Windows:

code
Bash
download
content_copy
expand_less
python -m venv venv
venv\Scripts\activate

Mac/Linux:

code
Bash
download
content_copy
expand_less
python3 -m venv venv
source venv/bin/activate

Install Python Dependencies:

code
Bash
download
content_copy
expand_less
pip install -r requirements.txt
Usage
Running the Application

You can run the application using the Python command directly within your virtual environment:

code
Bash
download
content_copy
expand_less
python app_gui.py

Alternatively, use the provided script files:

Windows: Double-click Start_App.bat.

Mac: Run Start_App.command.

Workflow

Upload Media: Accepts Video (.mp4, .mkv, .mov) or Audio (.mp3, .wav) files.

Keyword Input: Define a specific term (e.g., a name or technical topic). The application will index timestamps and extract video frames wherever this keyword occurs.

Prompt Configuration: Modify the system prompt to adjust the focus of the AI summarization (default is set for AV Project Management).

Generation: Clicking "Generate" will produce a web-based HTML report and enable the PDF download button.

Configuration

To change the LLM used for summarization, edit the app_gui.py file:

code
Python
download
content_copy
expand_less
# app_gui.py - Line 14
MODEL_NAME = "gemma3:4b"  # Change this to "llama3", "mistral", etc.

Ensure the corresponding model is installed via Ollama (ollama pull <model_name>).

Technical Stack

Transcription: OpenAI Whisper (Base model).

Inference/LLM: Ollama (Local API).

Computer Vision: OpenCV (Frame extraction).

Interface: Gradio.

PDF Generation: xhtml2pdf.

License

This project is open-source.
