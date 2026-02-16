# Phase 2: Audio Input Implementation Plan

## Goal
Add voice input to TARS display with wake word detection, audio visualization, and local STT.

## System Specs (lil-ark)
- **Hardware:** Raspberry Pi 5 Model B Rev 1.1
- **CPU:** 4 cores
- **RAM:** 8GB (6.5GB available)
- **Audio:** Pi Audio HAT (microphone + speakers)
- **Performance:** ✅ More than enough for local Whisper

## Architecture

```
Microphone (Always On)
  ↓
Wake Word Detection (Vosk - "Hey TARS")
  ↓ [Wake word detected]
UI: Switch to Listening Mode
  - Audio visualizer (waveform/bars)
  - Live transcription display
  ↓
Voice Activity Detection (webrtcvad)
  - Detect speech start/end
  - Buffer audio chunks
  - Stop on 1.5-2s pause
  ↓ [Pause detected]
whisper.cpp (Local STT - base model)
  - Transcribe buffered audio (~3-4s)
  ↓
Send text to OpenClaw via socket
  (Same path as keyboard input)
  ↓
Display: Back to response mode
  - Show TARS reply
```

## Components

### 1. Wake Word Detection
**Tool:** Vosk (Open source, runs locally)
- **Model:** vosk-model-small-en-us-0.15 (~40MB)
- **Wake phrase:** "Hey TARS" (configurable)
- **Latency:** <50ms detection time
- **CPU:** Minimal impact, always listening
- **Install:**
  ```bash
  pip3 install vosk
  wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
  unzip vosk-model-small-en-us-0.15.zip
  ```

### 2. Voice Activity Detection
**Tool:** webrtcvad (Google's VAD)
- **Purpose:** Detect when speech starts/stops
- **Pause threshold:** 1.5-2 seconds of silence = done speaking
- **Frame rate:** 30ms frames (optimal for VAD)
- **Install:** `pip3 install webrtcvad`

### 3. Local Speech-to-Text
**Tool:** whisper.cpp (Optimized C++ implementation)
- **Model:** base.en (English-only, fastest quality model)
  - Size: 142MB
  - Speed: ~3-4 seconds per utterance on Pi 5
  - Accuracy: Excellent for clear speech
- **Alternative models:**
  - tiny.en: Faster but less accurate
  - small.en: Better accuracy but slower
- **Install:**
  ```bash
  git clone https://github.com/ggerganov/whisper.cpp
  cd whisper.cpp
  make
  bash ./models/download-ggml-model.sh base.en
  ```
- **Usage:**
  ```bash
  ./main -m models/ggml-base.en.bin -f audio.wav
  ```
- **Python binding:** pywhispercpp or subprocess

### 4. Audio Visualization
**Tool:** PyQt5 + Custom painting or Matplotlib
- **Type:** Real-time waveform or bar visualizer
- **Update rate:** 30-60 FPS
- **Data:** Live audio buffer samples
- **Visual style:** Green waveform matching TARS aesthetic

### 5. Audio Capture
**Tool:** PyAudio
- **Sample rate:** 16kHz (optimal for Whisper)
- **Channels:** 1 (mono)
- **Format:** 16-bit PCM
- **Chunk size:** 480 samples (30ms frames for VAD)
- **Install:** `sudo apt-get install python3-pyaudio`

## UI Design

### State 1: Normal (Waiting for Wake Word)
```
┌─────────────────────────────────────────┐
│  TARS                                   │
│  ════════════════════════════════════   │
│                                         │
│  [Scrolling conversation history]       │
│                                         │
│  > Hello TARS!                          │
│                                         │
│  TARS: Hello! How can I help you?      │
│                                         │
│  ⚫ Listening...                         │
└─────────────────────────────────────────┘
```

### State 2: Listening (After "Hey TARS")
```
┌─────────────────────────────────────────┐
│  🎤 LISTENING                            │
│  ════════════════════════════════════   │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  ▁▃▅▇█▇▅▃▁ ▁▃▅▇█▇▅▃▁ ▁▃▅▇█▇      │  │
│  │          Audio Waveform            │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Transcribing...                       │
│  "What's the weather like today"       │
│                                         │
│  💬 Speak now (pause to finish)        │
└─────────────────────────────────────────┘
```

### State 3: Processing
```
┌─────────────────────────────────────────┐
│  🤖 PROCESSING                           │
│  ════════════════════════════════════   │
│                                         │
│  You: "What's the weather like today?" │
│                                         │
│  [Thinking...]                         │
│                                         │
└─────────────────────────────────────────┘
```

## File Structure

```
extensions/tars-channel/
├── display/
│   ├── tars_display.py          # Main display (current)
│   ├── audio_input.py           # NEW: Audio capture & processing
│   ├── wake_word.py             # NEW: Vosk wake word detection
│   ├── visualizer.py            # NEW: Audio visualization widget
│   ├── requirements.txt         # Update with new deps
│   └── models/
│       └── vosk-model-small/    # Wake word model
├── whisper.cpp/                 # NEW: Clone of whisper.cpp
│   ├── main                     # Compiled binary
│   └── models/
│       └── ggml-base.en.bin     # Whisper model
└── ...
```

## Implementation Steps

### Step 1: Install & Test Dependencies
```bash
# PyAudio
sudo apt-get install python3-pyaudio portaudio19-dev

# Python packages
pip3 install vosk webrtcvad numpy matplotlib

# Whisper.cpp
cd /home/tars/openclaw/extensions/tars-channel
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make -j4
bash ./models/download-ggml-model.sh base.en

# Test whisper
arecord -d 5 -f S16_LE -r 16000 test.wav
./main -m models/ggml-base.en.bin -f test.wav
```

### Step 2: Implement Wake Word Detection
**File:** `display/wake_word.py`
- Create WakeWordDetector class
- Load Vosk model
- Continuous audio stream processing
- Emit signal when "Hey TARS" detected

### Step 3: Implement VAD & Audio Buffering
**File:** `display/audio_input.py`
- AudioCapture class with PyAudio
- webrtcvad for speech detection
- Buffer audio chunks while speaking
- Detect pause (1.5s silence)
- Save buffer to WAV file

### Step 4: Integrate Whisper.cpp
**File:** `display/audio_input.py`
- Method to call whisper.cpp subprocess
- Parse output for transcription
- Handle errors gracefully
- Return text

### Step 5: Build Audio Visualizer
**File:** `display/visualizer.py`
- Custom QWidget for waveform display
- Real-time audio buffer visualization
- Green aesthetic matching TARS
- 30-60 FPS update rate

### Step 6: Integrate into Main Display
**File:** `display/tars_display.py`
- Add audio input module
- State management (normal/listening/processing)
- Switch UI based on state
- Show visualizer during listening
- Display transcription as it forms
- Send final text to OpenClaw socket

### Step 7: Update Requirements
**File:** `display/requirements.txt`
```
PyQt5>=5.15.0
vosk>=0.3.45
webrtcvad>=2.0.10
numpy>=1.21.0
pyaudio>=0.2.13
```

### Step 8: Test & Tune
- Test wake word accuracy
- Adjust VAD pause threshold
- Tune visualizer responsiveness
- Test Whisper transcription quality
- Measure end-to-end latency

## Performance Targets

- **Wake word detection:** <50ms
- **VAD pause detection:** 1.5-2 seconds
- **Whisper transcription:** 3-4 seconds
- **Total latency:** ~5-6 seconds from speech end to text ready
- **CPU usage:** <30% during transcription
- **RAM usage:** <500MB total

## Configuration

**File:** `display/audio_config.py`
```python
# Audio
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 480  # 30ms frames

# Wake word
WAKE_PHRASE = "hey tars"
VOSK_MODEL_PATH = "models/vosk-model-small"

# VAD
VAD_MODE = 3  # Aggressive filtering
PAUSE_THRESHOLD = 1.5  # Seconds

# Whisper
WHISPER_MODEL = "base.en"
WHISPER_PATH = "../whisper.cpp/main"

# Visualizer
VIS_FPS = 30
VIS_COLOR = "#00ff41"  # TARS green
```

## Error Handling

- **Microphone not available:** Show error, disable voice input
- **Wake word model missing:** Fallback to keyboard only
- **Whisper fails:** Show "transcription error", retry or fallback
- **Audio device errors:** Graceful recovery, user notification

## Testing Checklist

- [ ] Wake word triggers reliably
- [ ] False positive rate acceptable
- [ ] VAD detects speech accurately
- [ ] Pause detection works at 1.5s
- [ ] Whisper transcription is accurate
- [ ] Visualizer shows audio in real-time
- [ ] UI transitions smoothly between states
- [ ] Text sends to OpenClaw correctly
- [ ] No audio dropouts or glitches
- [ ] System remains responsive

## Future Enhancements

- Multiple wake phrases
- Volume/sensitivity adjustments via config
- Speech-to-speech with TTS response (Phase 3)
- Continuous conversation mode (no wake word after first)
- Background noise filtering
- Multi-language support

## References

- Vosk: https://alphacephei.com/vosk/
- whisper.cpp: https://github.com/ggerganov/whisper.cpp
- webrtcvad: https://github.com/wiseman/py-webrtcvad
- PyAudio: https://people.csail.mit.edu/hubert/pyaudio/

## Notes

- Keep wake word running in background thread (minimal CPU)
- Only activate Whisper after speech detected (save resources)
- Buffer entire utterance before transcribing (better accuracy)
- Use 16kHz audio for optimal Whisper performance
- Consider adding LED indicator for listening state (GPIO)
