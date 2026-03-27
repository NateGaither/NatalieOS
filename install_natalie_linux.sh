#!/bin/bash
echo "🐱 NatalieOS: Linux Installer starting..."

# 1. Install System Dependencies (Audio and PortAudio)
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip libasound2-dev libportaudio2 curl

# 2. Create Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating Virtual Environment..."
    python3 -m venv venv
fi

# 3. Activate and Install Python Requirements
source venv/bin/activate
echo "📥 Installing Python libraries..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Download Voice Assets (If missing)
if [ ! -f "kokoro-v0.19.onnx" ]; then
    echo "🎙️ Voice model missing. Downloading (300MB)..."
    curl -L "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0.19.onnx" -o "kokoro-v0.19.onnx"
fi

if [ ! -f "voices.json" ]; then
    echo "📁 Voice profiles missing. Downloading..."
    curl -L "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.json" -o "voices.json"
fi

# 5. Setup Environment
if [ ! -f ".env" ]; then
    echo "OPENROUTER_API_KEY=" > .env
    echo "⚠️ Created .env file. Please add your key!"
fi

echo -e "\n🎉 SETUP COMPLETE!"
echo "--------------------------------------------------"
echo "1. Put your key in .env"
echo "2. Run: source venv/bin/activate && python3 main.py"
echo "--------------------------------------------------"
