"""Audio configuration for TARS voice input."""

import os

# Get the directory of this config file
_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CONFIG_DIR)

# Audio settings
SAMPLE_RATE = 16000  # Hz - optimal for Whisper
CHANNELS = 1  # Mono
CHUNK_SIZE = 480  # 30ms frames (optimal for VAD)
FORMAT = 'int16'  # 16-bit PCM

# Wake word settings
WAKE_PHRASE = "hey tars"
VOSK_MODEL_PATH = os.path.join(_CONFIG_DIR, "models", "vosk-model-small")
WAKE_WORD_THRESHOLD = 0.7  # Confidence threshold

# Voice Activity Detection (VAD)
VAD_MODE = 3  # 0-3, 3 = most aggressive filtering
PAUSE_THRESHOLD = 1.5  # Seconds of silence before ending speech
SPEECH_START_FRAMES = 5  # Frames of speech to confirm start

# Whisper settings
WHISPER_MODEL = "base.en"
WHISPER_PATH = os.path.join(_PROJECT_ROOT, "whisper.cpp", "build", "bin", "whisper-cli")
WHISPER_MODEL_PATH = os.path.join(_PROJECT_ROOT, "whisper.cpp", "models", "ggml-base.en.bin")

# Visualizer settings
VIS_FPS = 30  # Frames per second for visualizer
VIS_COLOR = "#00ff41"  # TARS green
VIS_HISTORY = 100  # Number of amplitude samples to display

# Audio buffer settings
MAX_RECORDING_SECONDS = 30  # Maximum recording length
TEMP_AUDIO_PATH = "/tmp/tars_voice_input.wav"
