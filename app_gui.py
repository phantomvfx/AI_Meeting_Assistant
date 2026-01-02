import gradio as gr
import whisper
import ollama
import cv2
import os
import base64
import shutil
import atexit
from datetime import timedelta
from xhtml2pdf import pisa

# --- CONFIGURATION ---
MODEL_NAME = "gemma3:4b"  
TEMP_DIR = "temp_reports" 

os.makedirs(TEMP_DIR, exist_ok=True)

# --- CLEANUP ---
def cleanup_on_exit():
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
        except:
            pass

atexit.register(cleanup_on_exit)

# --- HELPER FUNCTIONS ---
def image_to_base64(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

def extract_frame_base64(video_path, seconds):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
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

def convert_html_to_pdf(source_html, output_filename):
    try:
        with open(output_filename, "wb") as result_file:
            pisa_status = pisa.CreatePDF(source_html, dest=result_file)
        return not pisa_status.err
    except Exception as e:
        print(f"PDF Gen Error: {e}")
        return False

# --- CSS STYLES ---

# 1. DARK THEME (For the Web UI)
CSS_DARK = """
<style>
    body { 
        font-family: 'Segoe UI', Roboto, Helvetica, sans-serif; 
        background-color: #0b0f19 !important; /* Matches Gradio Dark BG */
        color: #e5e7eb !important; /* Light Grey Text */
        padding: 0; margin: 0;
    }
    .report-container {
        padding: 20px;
        max-width: 100%;
    }
    h1 { 
        color: #60a5fa !important; /* Light Blue */
        border-bottom: 1px solid #374151; 
        padding-bottom: 15px; 
        font-weight: 600;
    }
    h2 { 
        color: #93c5fd !important; /* Lighter Blue */
        margin-top: 30px; 
        font-size: 1.2em;
        border-left: 4px solid #3b82f6;
        padding-left: 10px;
    }
    /* Cards */
    .summary-box, .mention, .transcript {
        background-color: #1f2937 !important; /* Dark Grey Card */
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 20px;
        margin-top: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    .mention {
        border-left: 4px solid #f59e0b; /* Amber/Gold accent for mentions */
    }
    .timestamp {
        color: #f59e0b;
        font-weight: bold;
        margin-bottom: 5px;
        display: block;
    }
    .transcript {
        color: #9ca3af !important; /* Dimmed text for transcript */
        font-family: monospace;
        font-size: 0.9em;
        height: 200px;
        overflow-y: auto;
    }
    img {
        border-radius: 4px;
        margin-top: 10px;
        border: 1px solid #4b5563;
    }
</style>
"""

# 2. LIGHT THEME (For the PDF File)
CSS_LIGHT = """
<style>
    @page { size: A4; margin: 1cm; }
    body { 
        font-family: Helvetica, sans-serif; 
        background-color: #ffffff; 
        color: #333333; 
    }
    h1 { color: #1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; }
    h2 { color: #1d4ed8; margin-top: 25px; background-color: #eff6ff; padding: 5px; }
    .summary-box { background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 10px; }
    .mention { background-color: #fffbeb; border: 1px solid #e2e8f0; padding: 10px; margin-bottom: 10px; }
    .timestamp { color: #d97706; font-weight: bold; }
    .transcript { font-size: 10px; color: #64748b; }
</style>
"""

# --- MAIN PROCESS LOGIC ---
def process_meeting(file_obj, keyword, custom_prompt, progress=gr.Progress()):
    if file_obj is None:
        return "Please upload a file.", None, None

    file_path = file_obj.name
    filename = os.path.basename(file_path)
    file_prefix = os.path.splitext(filename)[0]
    
    # 1. TRANSCRIBE
    progress(0.1, desc="🎧 Transcribing...")
    model = whisper.load_model("base")
    result = model.transcribe(file_path, fp16=False)
    
    full_text = result['text']
    segments = result['segments']
    
    # 2. FIND MENTIONS
    progress(0.4, desc=f"🔍 Searching for '{keyword}'...")
    mentions_body = ""
    found_count = 0
    
    for segment in segments:
        if keyword.lower() in segment['text'].lower():
            found_count += 1
            start_seconds = segment['start']
            time_str = str(timedelta(seconds=int(start_seconds)))
            
            img_tag = ""
            if is_video_file(file_path):
                b64_str = extract_frame_base64(file_path, start_seconds)
                if b64_str:
                    img_tag = f'<br><img src="data:image/jpeg;base64,{b64_str}" style="width:400px; height:auto;">'
            
            mentions_body += f"""
            <div class='mention'>
                <span class="timestamp">⏱ Time: {time_str}</span>
                <div>"{segment['text']}"</div>
                {img_tag}
            </div>
            """
    
    if found_count == 0:
        mentions_body = "<p>No matches found for this keyword.</p>"

    # 3. SUMMARIZE
    progress(0.7, desc="🤖 AI Summarizing...")
    hidden_rules = """
    STRICT OUTPUT RULES:
    1. Output ONLY the report content.
    2. Do NOT write fillers like "Here is the summary".
    3. Do NOT ask follow-up questions.
    """
    final_prompt = f"{hidden_rules}\n\n{custom_prompt}\n\nTRANSCRIPT DATA:\n{full_text[:8000]}"
    
    try:
        response = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': final_prompt}])
        ai_summary = response['message']['content']
        # Clean fillers
        fillers = ["Do you want me to elaborate", "Let me know", "I hope this helps", "Here is the analysis"]
        for phrase in fillers:
            ai_summary = ai_summary.replace(phrase, "")
        ai_summary = ai_summary.replace("\n", "<br>")
    except Exception as e:
        ai_summary = f"<span style='color:red'>Error connecting to Ollama: {e}</span>"

    # 4. BUILD CONTENT BODY (Reusable)
    body_content = f"""
        <h1>Meeting Analysis: {filename}</h1>
        
        <h2>Executive Summary</h2>
        <div class="summary-box">{ai_summary}</div>

        <h2>Mentions of "{keyword}" ({found_count})</h2>
        {mentions_body}

        <h2>Full Transcript</h2>
        <div class="transcript">{full_text}</div>
    """

    # 5. GENERATE FINAL OUTPUTS
    progress(0.9, desc="📝 Rendering...")
    
    # Version A: Dark Mode (For Screen)
    html_dark = f"<!DOCTYPE html><html><head>{CSS_DARK}</head><body><div class='report-container'>{body_content}</div></body></html>"
    
    # Version B: Light Mode (For PDF)
    html_light = f"<!DOCTYPE html><html><head>{CSS_LIGHT}</head><body>{body_content}</body></html>"
    
    # Save Files
    html_filename = os.path.join(TEMP_DIR, f"Report_{file_prefix}.html")
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_dark) # We save the dark version to disk for viewing

    pdf_filename = os.path.join(TEMP_DIR, f"Report_{file_prefix}.pdf")
    convert_html_to_pdf(html_light, pdf_filename) # We convert the LIGHT version to PDF
        
    return html_dark, pdf_filename, [html_filename, pdf_filename]

# --- RESET LOGIC ---
def reset_app(file_paths_list):
    if file_paths_list:
        for file_path in file_paths_list:
            if os.path.exists(file_path):
                try: os.remove(file_path)
                except: pass
    return None, "Manu", default_prompt, "", None, None

# --- GUI LAYOUT ---
default_prompt = """
You are an expert AV Project Manager. Analyze the transcript below.
1. Write a concise executive summary.
2. Extract a list of Action Items (who needs to do what).
3. Highlight any technical specifications mentioned (cables, resolution, software).
"""

with gr.Blocks(title="AI Meeting Assistant", theme=gr.themes.Soft()) as demo:
    
    current_files_state = gr.State(value=[])
    
    gr.Markdown("# 🎥 AI Meeting Assistant")
    
    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(label="Upload Media", file_types=["video", "audio"])
            keyword_input = gr.Textbox(label="Keyword / Name", value="Manu")
            prompt_input = gr.Textbox(label="AI Instructions", value=default_prompt, lines=5)
            
            with gr.Row():
                submit_btn = gr.Button("🚀 Generate Report", variant="primary")
                reset_btn = gr.Button("🗑️ Reset & Delete", variant="stop")
            
            pdf_download_btn = gr.DownloadButton(label="📥 Download PDF", value=None)
        
        with gr.Column(scale=2):
            output_html = gr.HTML(label="Report Preview")

    submit_btn.click(
        fn=process_meeting,
        inputs=[file_input, keyword_input, prompt_input],
        outputs=[output_html, pdf_download_btn, current_files_state] 
    )
    
    reset_btn.click(
        fn=reset_app,
        inputs=[current_files_state],
        outputs=[file_input, keyword_input, prompt_input, output_html, pdf_download_btn, current_files_state]
    )

if __name__ == "__main__":
    demo.launch(inbrowser=True)