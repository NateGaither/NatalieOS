import threading, time, os, pygame, requests, json
import numpy as np
import sounddevice as sd
from kokoro_onnx import KokoroONNX
from flask import Flask, render_template, jsonify
from faster_whisper import WhisperModel
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import psutil, win32gui, win32process

# --- CONFIGURATION ---
L3_BUTTON = 8           # Controller Button ID
OLLAMA_MODEL = "llama3" # Ensure this is pulled in Ollama
V_CABLE_NAME = "CABLE Input"
PORT = 5000

# Global State
state = {
    "sass": 50,
    "cute": 50,
    "status": "IDLE",
    "game": "Desktop",
    "last_response": "System Ready...",
    "history": []
}

# --- INITIALIZE MODELS ---
# Note: Ensure kokoro-v0.19.onnx and voices.json are in the folder
tts = KokoroONNX("kokoro-v0.19.onnx", "voices.json")
whisper_model = WhisperModel("base", device="cuda", compute_type="float16")

# --- UTILITIES ---
def set_mute(mute=True):
    """Mutes the physical system microphone for stealth."""
    try:
        devices = AudioUtilities.GetMicrophone()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(1 if mute else 0, None)
    except: pass

def get_active_game():
    """Detects what window you are currently looking at."""
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name().replace(".exe", "")
    except: return "Desktop"

def speak(text):
    """Generates audio and routes it to the Virtual Cable."""
    samples, sample_rate = tts.create(text, voice="af_bella", speed=1.1)
    devices = sd.query_devices()
    cable_id = next((i for i, d in enumerate(devices) if V_CABLE_NAME in d['name']), None)
    if cable_id is not None:
        sd.play(samples, sample_rate, device=cable_id)
        sd.wait()

def ask_ollama(user_input):
    """Sends the instructions.txt + history + input to Ollama."""
    with open("instructions.txt", "r") as f:
        # Pass current state into the instructions template
        system_prompt = f.read().format(
            game=state["game"],
            sass=state["sass"],
            cute=state["cute"],
            history="\n".join([f"User: {m['u']}\nNatalie: {m['n']}" for m in state["history"]])
        )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{system_prompt}\nUser: {user_input}\nResponse (JSON):",
        "format": "json",
        "stream": False
    }
    
    try:
        r = requests.post("http://localhost:11434/api/generate", json=payload)
        return json.loads(r.json().get("response", "{}"))
    except:
        return {"sass": state["sass"], "cute": state["cute"], "response": "Brain error! Check Ollama."}

# --- WEB SERVER ---
app = Flask(__name__)
@app.route('/')
def index(): return render_template('dashboard.html')
@app.route('/stats')
def stats(): return jsonify(state)

# --- MAIN LOOP ---
def main():
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("Error: No controller detected!")
        return
    joy = pygame.joystick.Joystick(0)
    joy.init()

    print("Natalie OS Active. Connect phone to Dashboard to begin.")

    while True:
        pygame.event.pump()
        state["game"] = get_active_game()

        if joy.get_button(L3_BUTTON):
            state["status"] = "LISTENING"
            set_mute(True) # Stealth mute ON
            
            # Record Audio
            fs, rec = 16000, []
            while joy.get_button(L3_BUTTON):
                chunk = sd.rec(int(0.2 * fs), samplerate=fs, channels=1); sd.wait()
                rec.append(chunk)
            
            state["status"] = "THINKING"
            audio = np.concatenate(rec, axis=0).flatten()
            segments, _ = whisper_model.transcribe(audio)
            user_text = " ".join([s.text for s in segments]).strip()

            if user_text:
                # Process through Ollama
                ai_data = ask_ollama(user_text)
                
                # Update global state from AI JSON output
                state["sass"] = ai_data.get("sass", state["sass"])
                state["cute"] = ai_data.get("cute", state["cute"])
                state["last_response"] = ai_data.get("response", "...")

                # Speak
                state["status"] = "SPEAKING"
                speak(state["last_response"])
                
                # Save to Memory
                state["history"].append({"u": user_text, "n": state["last_response"]})
                if len(state["history"]) > 10: state["history"].pop(0)

            set_mute(False) # Stealth mute OFF
            state["status"] = "IDLE"
        
        time.sleep(0.05)

if __name__ == '__main__':
    # Ensure templates folder exists
    if not os.path.exists('templates'): os.makedirs('templates')
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, use_reloader=False)).start()
    main()
