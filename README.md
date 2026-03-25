# NatalieOS
🐱 Natalie OS v2.0
The Stealth AI Companion for VRChat

Natalie is a local-hosted AI cat-girl integrated directly into VRChat via OSC and Virtual Audio Routing. She features a private phone-based dashboard, voice-to-voice interaction triggered by a controller, and a persistent memory of her "friends" and enemies.

🚀 Features
Physical Trigger: Hold L3 (Left Stick Click) to whisper. Your system mic mutes automatically so nobody in-game hears you.

Local Brain: Powered by Ollama (Llama 3). No cloud fees, 100% private.

Fastest Voice: Uses Kokoro-82M for sub-200ms text-to-speech response.

Phone HUD: A web-based dashboard to track Sass/Cute levels and read transcripts in real-time.

Game Awareness: Automatically detects if you are in VRChat or another game and adjusts her personality.

🛠️ Installation
1. Hardware/Drivers
VB-Audio Cable: Download here.

Set CABLE Input as the AI's output.

Set CABLE Output as VRChat's Microphone.

NVIDIA GPU: Recommended for Faster-Whisper and Ollama.

2. Software
Install Ollama: ollama run llama3

Install Python Dependencies:

Bash

pip install pygame faster-whisper flask requests sounddevice kokoro-onnx pycaw comtypes psutil
3. Folder Structure
Plaintext

/NatalieProject
├── natalie_pro.py        # The Master Script
├── instructions.txt      # Personality & Lore (Edit this!)
├── kokoro-v0.19.onnx     # TTS Model
├── voices.json           # TTS Voice Library
└── templates/
    └── dashboard.html    # Phone HUD UI
🎮 How to Use
Launch Ollama.

Run the script: python natalie_pro.py.

Connect Phone: Open your phone browser to http://[YOUR-PC-IP]:5000.

In VRChat: * Find Aries or Siri.

Click and hold L3.

Whisper: "Natalie, roast Aries' new avatar."

Release L3 and wait for the chaos.

📝 Editing the Personality
Open instructions.txt to change how Natalie acts.

Sass/Cute: Use the {sass} and {cute} tags in the text.

Lore: Add names of people you hang out with so she remembers them.

Memory: The script automatically appends the last 10 messages to the prompt.

⚠️ Troubleshooting
Mic not muting? Run the script as Administrator.

No sound in VRChat? Check that "CABLE Output" is selected in the VRChat Audio menu.

Laggy response? Ensure compute_type="float16" is set in the Whisper settings for GPU acceleration.
