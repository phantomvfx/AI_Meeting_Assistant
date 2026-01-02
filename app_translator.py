import gradio as gr
import whisper
import ollama
import cv2
import os
import base64
import shutil
import atexit
from datetime import timedelta

# --- CONFIGURATION ---
# gemma2/3 or llama3 work well for translation. 
# If you want even better Japanese, try 'qwen2:7b' or 'gemma2:9b' via Ollama.
MODEL_NAME = "gemma3:4b"  
TEMP_DIR = "temp_translation" 

os.makedirs(TEMP_DIR, exist_ok=True)

# --- CLEANUP ---
def cleanup_on_exit():
    if os.path.exists(TEMP_DIR):
        try: shutil.rmtree(TEMP_DIR)
        except: pass

atexit.register(cleanup_on_exit)

# --- HELPER FUNCTIONS ---
def image_to_base64(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

def extract_frame_base64(video_path, seconds):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened(): return None
    cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
    success, image = cap.read()
    cap.release()
    if success:
        image = cv2.resize(image, (640, 360)) 
        return image_to_base64(image)
    return None

def is_video_file(filename):
    video_exts = ('.mp4', '.mkv', '.mov', '.avi', '.webm')
    return filename.lower().endswith(video_exts)

# --- TRANSLATION LOGIC ---
def process_translation(file_obj, keyword, custom_prompt, progress=gr.Progress()):
    if file_obj is None:
        return "Please upload a file.", None

    file_path = file_obj.name
    filename = os.path.basename(file_path)
    file_prefix = os.path.splitext(filename)[0]
    
    # 1. TRANSCRIBE (Force Spanish)
    progress(0.1, desc="🎧 Escuchando (Transcribing Spanish)...")
    model = whisper.load_model("base")
    
    # Force language to Spanish for better accuracy
    result = model.transcribe(file_path, fp16=False, language="es")
    
    full_text_es = result['text']
    segments = result['segments']
    
    # 2. FIND MENTIONS (In Spanish Audio)
    progress(0.4, desc=f"🔍 Searching for '{keyword}'...")
    mentions_html = ""
    found_count = 0
    
    for segment in segments:
        # Search for the keyword in the Spanish text
        if keyword.lower() in segment['text'].lower():
            found_count += 1
            start_seconds = segment['start']
            time_str = str(timedelta(seconds=int(start_seconds)))
            
            img_tag = ""
            if is_video_file(file_path):
                b64_str = extract_frame_base64(file_path, start_seconds)
                if b64_str:
                    img_tag = f'<br><img src="data:image/jpeg;base64,{b64_str}" style="width:400px; height:auto; margin-top:5px; border:1px solid #333;">'
            
            mentions_html += f"""
            <div class='mention'>
                <span class="timestamp">⏱ {time_str}</span>
                <div>"{segment['text']}"</div>
                {img_tag}
            </div>
            """
    
    if found_count == 0:
        mentions_html = "<p>No matches found.</p>"

    # 3. TRANSLATE & SUMMARIZE (ES -> JP)
    progress(0.7, desc="🤖 Traduciento a Japonés (Translating)...")
    
    # Specific Translation Rules
    hidden_rules = """
    ROLE: Professional Interpreter (Spanish to Japanese).
    TASK: Analyze the provided SPANISH transcript and output the report in JAPANESE.
    RULES:
    1. Output ONLY the report content in Japanese (Kanji/Kana).
    2. Do NOT provide conversational fillers.
    3. Translate the core meaning accurately.
    4. Structure: Executive Summary, Action Items, Technical Specs.
    """
    
    final_prompt = f"{hidden_rules}\n\nUSER INSTRUCTION: {custom_prompt}\n\nSPANISH TRANSCRIPT:\n{full_text_es[:8000]}"
    
    try:
        response = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': final_prompt}])
        jp_summary = response['message']['content']
        jp_summary = jp_summary.replace("\n", "<br>")
    except Exception as e:
        jp_summary = f"<span style='color:red'>Error connecting to Ollama: {e}</span>"

    # 4. GENERATE HTML (Dark Mode)
    progress(0.9, desc="📝 Rendering Report...")
    
    html_report = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ 
                font-family: 'Noto Sans JP', 'Hiragino Kaku Gothic Pro', 'Meiryo', sans-serif; 
                background-color: #0b0f19; 
                color: #e5e7eb; 
                padding: 20px;
            }}
            .container {{ max-width: 900px; margin: auto; }}
            h1 {{ color: #ef4444; border-bottom: 1px solid #374151; padding-bottom: 15px; }} /* Red for Japan theme */
            h2 {{ color: #fca5a5; margin-top: 30px; border-left: 4px solid #ef4444; padding-left: 10px; }}
            .box {{ background-color: #1f2937; border: 1px solid #374151; padding: 20px; border-radius: 8px; margin-top: 10px; }}
            .mention {{ background-color: #1f2937; border-left: 4px solid #f59e0b; padding: 15px; margin-bottom: 15px; }}
            .timestamp {{ color: #f59e0b; font-weight: bold; display: block; margin-bottom: 5px; }}
            .transcript {{ color: #9ca3af; font-size: 0.9em; height: 200px; overflow-y: auto; font-family: monospace; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🇯🇵 Meeting Translation: {filename}</h1>
            
            <h2>AI Executive Summary (Japanese)</h2>
            <div class="box">{jp_summary}</div>

            <h2>Keyword Hits: "{keyword}" (Original Audio)</h2>
            {mentions_html}

            <h2>Original Spanish Transcript</h2>
            <div class="box transcript">{full_text_es}</div>
        </div>
    </body>
    </html>
    """
    
    # Save HTML
    save_path = os.path.join(TEMP_DIR, f"Translation_{file_prefix}.html")
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html_report)
        
    return html_report, save_path

# --- RESET LOGIC ---
def reset_app(file_path):
    if file_path and os.path.exists(file_path):
        try: os.remove(file_path)
        except: pass
    return None, "Presupuesto", default_prompt, "", None

# --- GUI LAYOUT ---
default_prompt = """
Analyze this Spanish meeting.
1. Provide a summary in Japanese (日本語).
2. List Action Items in Japanese.
3. List Technical Requirements in Japanese.
"""

with gr.Blocks(title="AI Spanish -> Japanese Translator", theme=gr.themes.Soft()) as demo:
    
    current_file_state = gr.State(value=None)
    
    gr.Markdown("# 🇯🇵 AI Spanish-to-Japanese Translator")
    
    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(label="Upload Spanish Media (Audio/Video)")
            keyword_input = gr.Textbox(label="Keyword (In Spanish)", value="Presupuesto")
            prompt_input = gr.Textbox(label="Instructions", value=default_prompt, lines=5)
            
            with gr.Row():
                submit_btn = gr.Button("⛩️ Translate", variant="primary")
                reset_btn = gr.Button("🗑️ Reset", variant="stop")
        
        with gr.Column(scale=2):
            output_html = gr.HTML(label="Translation Report")

    submit_btn.click(
        fn=process_translation,
        inputs=[file_input, keyword_input, prompt_input],
        outputs=[output_html, current_file_state]
    )
    
    reset_btn.click(
        fn=reset_app,
        inputs=[current_file_state],
        outputs=[file_input, keyword_input, prompt_input, output_html, current_file_state]
    )

if __name__ == "__main__":
    demo.launch(inbrowser=True)