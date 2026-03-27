import threading, time, os, requests, json, pygame
import numpy as np
import sounddevice as sd
from kokoro_onnx import Kokoro
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv, set_key
from datetime import datetime

# --- 1. CONFIG & PATHS ---
ENV_FILE = ".env"
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def get_or_set_key():
    load_dotenv(ENV_FILE)
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        key = input("\n🔑 Enter OpenRouter API Key: ").strip()
        set_key(ENV_FILE, "OPENROUTER_API_KEY", key)
    return key

OPENROUTER_KEY = get_or_set_key()
CLOUD_MODEL = "liquid/lfm-2.5-1.2b-instruct:free" 
LOCAL_MODEL = "llama3.2:3b"
PORT = 5000

# --- 2. PERSISTENCE LOGIC ---
def get_log_file():
    return os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.json")

def save_to_disk(entry):
    file_path = get_log_file()
    data = []
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try: data = json.load(f)
            except: data = []
    
    data.append(entry)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def load_recent_memory(limit=5):
    """Loads the last X messages from today's log for AI context."""
    file_path = get_log_file()
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        try:
            data = json.load(f)
            return [{"u": d["user"], "n": d["natalie"]} for d in data[-limit:]]
        except:
            return []

# Initialize State
state = {
    "sass": 50, "cute": 50, "status": "IDLE", "brain": "Initializing...",
    "short_memory": load_recent_memory(), # Load from disk on startup
    "stats": {"total_turns": 0}
}

# --- 3. HARDWARE & TTS ---
def has_gpu():
    try:
        import subprocess
        subprocess.check_output(['nvidia-smi'], stderr=subprocess.STDOUT)
        return True
    except: return False

GPU_AVAILABLE = has_gpu()
sd.default.device = 0 

try:
    tts = Kokoro("kokoro-v0.19.onnx", "voices.json")
    print("✅ TTS & Memory Loaded")
except Exception as e:
    tts = None

# --- 4. THE BRAIN ---
def ask_ai(user_input):
    start_time = time.time()
    with open("instructions.txt", "r") as f:
        template = f.read()
    
    history_text = "\n".join([f"U: {h['u']} N: {h['n']}" for h in state["short_memory"]])
    system_info = template.format(
        game="Desktop", sass=state["sass"], cute=state["cute"], history=history_text
    )

    response_text = "Brain error..."
    
    # Try Local
    if GPU_AVAILABLE:
        try:
            state["brain"] = f"LOCAL ({LOCAL_MODEL})"
            r = requests.post("http://localhost:11434/api/chat", json={
                "model": LOCAL_MODEL,
                "messages": [{"role": "system", "content": system_info}, {"role": "user", "content": user_input}],
                "stream": False
            }, timeout=5)
            response_text = r.json()['message']['content']
        except: pass

    # Fallback Cloud
    if "LOCAL" not in state["brain"]:
        try:
            state["brain"] = f"CLOUD ({CLOUD_MODEL})"
            headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": CLOUD_MODEL,
                "messages": [{"role": "system", "content": system_info}, {"role": "user", "content": user_input}]
            }
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=15)
            response_text = r.json()['choices'][0]['message']['content']
        except Exception as e:
            response_text = f"Error: {e}"

    latency = round(time.time() - start_time, 2)
    return response_text, latency

# --- 5. INTERACTION ---
def process_interaction(user_text):
    if not user_text.strip(): return
    state["status"] = "THINKING"
    
    raw_response, latency = ask_ai(user_text)
    clean_text = raw_response.replace("Natalie:", "").strip()
    
    # Mood Logic
    low = clean_text.lower()
    if any(w in low for w in ["ugh", "dummy", "stop"]): state["sass"] = min(100, state["sass"] + 10)
    if any(w in low for w in [":3", "pats", "cute"]): state["cute"] = min(100, state["cute"] + 10)

    # 💾 SAVE TO FILESYSTEM
    log_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "user": user_text,
        "natalie": clean_text,
        "latency": latency,
        "brain": state["brain"],
        "mood": {"sass": state["sass"], "cute": state["cute"]}
    }
    save_to_disk(log_entry)

    # Update state
    state["short_memory"].append({"u": user_text, "n": clean_text})
    if len(state["short_memory"]) > 5: state["short_memory"].pop(0)
    state["status"] = "SPEAKING"
    
    print(f"[{state['brain']}] Natalie: {clean_text}")
    
    if tts:
        try:
            samples, sample_rate = tts.create(clean_text, voice="af_bella", speed=1.1)
            sd.play(samples, sample_rate)
            sd.wait()
        except: pass

    state["status"] = "IDLE"

# --- 6. SERVER ---
app = Flask(__name__)

@app.route('/stats')
def stats(): return jsonify(state)

@app.route('/history')
def history():
    file_path = get_log_file()
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route('/manual', methods=['POST'])
def manual_trigger():
    text = request.json.get("text", "")
    threading.Thread(target=process_interaction, args=(text,)).start()
    return jsonify({"status": "sent"})

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    print(f"🚀 NatalieOS Persistent: http://localhost:{PORT}")
    while True: time.sleep(1)
