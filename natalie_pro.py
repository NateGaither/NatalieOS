import threading, time, os, requests, json, pygame
import numpy as np
import sounddevice as sd
from kokoro_onnx import Kokoro
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv, set_key # pip install python-dotenv

# --- 1. KEY MANAGEMENT ---
ENV_FILE = ".env"

def get_or_set_key():
    load_dotenv(ENV_FILE)
    key = os.getenv("OPENROUTER_API_KEY")
    
    if not key or key.strip() == "":
        print("\n🔑 Natalie needs a brain! (OpenRouter API Key missing)")
        print("Get one for free at: https://openrouter.ai/keys")
        key = input("Please enter your API Key: ").strip()
        
        # Save it to .env so the user doesn't have to enter it next time
        set_key(ENV_FILE, "OPENROUTER_API_KEY", key)
        print("✅ Key saved to .env file!\n")
    
    return key

# Initialize Configuration
OPENROUTER_KEY = get_or_set_key()
CLOUD_MODEL = "liquid/lfm-2.5-1.2b-instruct:free" 
LOCAL_MODEL = "llama3.2:3b"
PORT = 5000

state = {
    "sass": 50, "cute": 50, "status": "IDLE", "game": "Desktop",
    "last_response": "System Online...", "history": [],
    "brain": "Initializing..."
}

# --- 2. HARDWARE & AUDIO ---
def has_gpu():
    try:
        import subprocess
        subprocess.check_output(['nvidia-smi'], stderr=subprocess.STDOUT)
        return True
    except: return False

GPU_AVAILABLE = has_gpu()
sd.default.device = 0 

# --- 3. TTS INITIALIZATION ---
try:
    tts = Kokoro("kokoro-v0.19.onnx", "voices.json")
    print("✅ TTS Model Loaded")
except Exception as e:
    print(f"❌ TTS Load Failed: {e}")
    tts = None

# --- 4. THE BRAIN ---
def ask_ai(user_input):
    with open("instructions.txt", "r") as f:
        template = f.read()
    
    recent_history = state["history"][-5:]
    history_text = "\n".join([f"U: {h['u']} N: {h['n']}" for h in recent_history])
    
    system_info = template.format(
        game=state["game"], sass=state["sass"], cute=state["cute"], history=history_text
    )

    if GPU_AVAILABLE:
        try:
            state["brain"] = f"LOCAL ({LOCAL_MODEL})"
            r = requests.post("http://localhost:11434/api/chat", json={
                "model": LOCAL_MODEL,
                "messages": [{"role": "system", "content": system_info}, {"role": "user", "content": user_input}],
                "stream": False
            }, timeout=5)
            return r.json()['message']['content']
        except: pass

    try:
        state["brain"] = f"CLOUD ({CLOUD_MODEL})"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "NatalieOS",
            "Content-Type": "application/json"
        }
        payload = {
            "model": CLOUD_MODEL,
            "messages": [
                {"role": "system", "content": system_info},
                {"role": "user", "content": user_input}
            ]
        }
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        else:
            return f"Error {r.status_code}: Please check your API key in .env"
    except Exception as e:
        return f"System Error: {e}"

# --- 5. INTERACTION & AUDIO ---
def process_interaction(user_text):
    if not user_text.strip(): return
    state["status"] = "THINKING"
    
    raw_response = ask_ai(user_text)
    clean_text = raw_response.replace("Natalie:", "").strip()
    
    # Simple Mood Logic
    low = clean_text.lower()
    if any(w in low for w in ["ugh", "dummy", "stop"]): state["sass"] = min(100, state["sass"] + 10)
    if any(w in low for w in [":3", "pats", "cute"]): state["cute"] = min(100, state["cute"] + 10)

    state["last_response"] = clean_text
    state["status"] = "SPEAKING"
    
    print(f"[{state['brain']}] Natalie: {clean_text}")
    if tts:
        try:
            samples, sample_rate = tts.create(clean_text, voice="af_bella", speed=1.1)
            sd.play(samples, sample_rate)
            sd.wait()
        except: pass

    state["history"].append({"u": user_text, "n": clean_text})
    state["status"] = "IDLE"

# --- 6. FLASK SERVER ---
app = Flask(__name__, template_folder=os.path.abspath('templates'), static_folder=os.path.abspath('static'))

@app.route('/')
def index(): return render_template('dashboard.html')

@app.route('/stats')
def stats(): return jsonify(state)

@app.route('/manual', methods=['POST'])
def manual_trigger():
    text = request.json.get("text", "")
    threading.Thread(target=process_interaction, args=(text,)).start()
    return jsonify({"status": "sent"})

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    print(f"🚀 Dashboard: http://localhost:{PORT}")
    while True: time.sleep(1)
