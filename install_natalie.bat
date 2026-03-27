@echo off
setlocal
echo 🐱 NatalieOS: Universal Installer starting...

:: 1. Create Virtual Environment
if not exist venv (
    echo 📦 Creating Virtual Environment...
    python -m venv venv
)

:: 2. Activate and Install
call venv\Scripts\activate
echo 📥 Installing Python libraries...
pip install --upgrade pip
pip install -r requirements.txt

:: 3. Download Voice Assets (If missing)
if not exist "kokoro-v0.19.onnx" (
    echo 🎙️ Voice model missing. Downloading (300MB)...
    curl -L "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0.19.onnx" -o "kokoro-v0.19.onnx"
)

if not exist "voices.json" (
    echo 📁 Voice profiles missing. Downloading...
    curl -L "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.json" -o "voices.json"
)

:: 4. Setup Environment
if not exist .env (
    echo OPENROUTER_API_KEY= > .env
    echo ⚠️ Created .env file. Open it and paste your OpenRouter key!
)

if not exist instructions.txt (
    echo 📝 Creating default instructions.txt...
    echo You are Natalie, a sassy desk pet. Game: {game}, Sass: {sass}, Cute: {cute}. History: {history} > instructions.txt
)

echo.
echo 🎉 SETUP COMPLETE!
echo --------------------------------------------------
echo 1. Paste your key into the .env file.
echo 2. Run Natalie with: venv\Scripts\python main.py
echo --------------------------------------------------
pause
