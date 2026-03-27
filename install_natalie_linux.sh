#!/bin/bash

# --- CONFIG ---
APP_NAME="NatalieOS"
PYTHON_BIN="python3"
VENV_DIR="venv"
LOG_DIR="logs"
PORT=5000

echo "🐱 Starting $APP_NAME automated deployment..."

# 1. System Dependency Check
echo "📦 Checking system packages (sudo may be required)..."
sudo apt-get update -y && sudo apt-get install -y \
    python3-venv python3-pip libasound2-dev libportaudio2 curl git ffmpeg

# 2. Directory & Structure
mkdir -p $LOG_DIR
mkdir -p templates
echo "📂 Directory structure verified."

# 3. Python Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 Creating virtual environment..."
    $PYTHON_BIN -m venv $VENV_DIR
fi
source $VENV_DIR/bin/activate

# 4. Install Requirements
echo "📥 Installing Python libraries..."
pip install --upgrade pip
cat <<EOF > requirements.txt
flask
requests
python-dotenv
numpy
sounddevice
pygame
soundfile
kokoro-onnx
onnxruntime
EOF
pip install -r requirements.txt

# 5. Fetch Voice Assets
if [ ! -f "kokoro-v0.19.onnx" ]; then
    echo "🎙️ Downloading Kokoro Voice Model (300MB)..."
    curl -L "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0.19.onnx" -o "kokoro-v0.19.onnx"
fi
if [ ! -f "voices.json" ]; then
    curl -L "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.json" -o "voices.json"
fi

# 6. Verify Environment File
if [ ! -f ".env" ] || [ -z "$(grep OPENROUTER_API_KEY .env)" ]; then
    echo "🔑 API Key required!"
    read -p "Enter your OpenRouter API Key: " user_key
    echo "OPENROUTER_API_KEY=$user_key" > .env
    echo "✅ Key saved to .env"
fi

# 7. Final Launch
echo -e "\n✨ Setup Complete! Launching Natalie..."
echo "📊 Access Dashboard at: http://localhost:$PORT"
echo "------------------------------------------------"
python3 main.py
