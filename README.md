# AI Voice Generator

A local text-to-speech application with natural pauses and emotional expression. No internet required after setup.

## Features

- Natural pauses based on punctuation (commas, periods, questions, etc.)
- Emotion detection (happy, sad, serious, excited, etc.)
- Multiple voices for English and Hindi
- Modern GUI interface
- Auto-generated filenames with date/time
- 100% local - no API calls, no data sent anywhere

## Quick Start (Windows)

1. **Download** this repository from GitHub
2. **Double-click** `launch_gui.bat`
3. Wait for first-time setup (installs dependencies + downloads voices)
4. The GUI will open automatically

That's it! Just type text and click "Generate Speech".

## Requirements

- **Python 3.10+** (must be added to PATH during install)
- **Windows 10/11** (also works on macOS/Linux with minor changes)

## Manual Setup

If the launcher doesn't work:

```bash
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download voice models
python download_models.py

# Launch GUI
python gui.py
```

## Usage

### GUI Mode
```bash
python gui.py
```

### Command Line Mode
```bash
# Direct text
python tts.py "Hello world" output.wav en

# From text file
python tts.py myfile.txt output.wav en

# Hindi
python tts.py "नमस्ते दुनिया" output.wav hi
```

## Available Voices

| Language | Voice | Quality |
|----------|-------|---------|
| English | Lessac (default) | Medium |
| English | Amy | Medium |
| English | LibriTTS | Medium |
| Hindi | Pratham (default) | Medium |
| Hindi | Priyamvada | Medium |

## How It Works

1. **Text Preprocessing** - Splits text into sentences and detects emotion
2. **Pause Generation** - Adds natural silence based on punctuation
3. **Voice Synthesis** - Each sentence synthesized with appropriate speed/volume
4. **Audio Concatenation** - All segments combined into final WAV file

## Project Structure

```
ai-voice-generator/
├── gui.py                  # Main GUI application
├── tts.py                  # Core TTS engine
├── download_models.py      # Downloads essential voices
├── download_extra_voices.py # Downloads additional voices
├── launch_gui.bat          # Windows launcher (auto-setup)
├── requirements.txt        # Python dependencies
├── models/                 # Voice models (downloaded)
└── output/                 # Generated audio files
```

## License

MIT License - Free to use and modify.
