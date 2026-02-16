# Audio Input Setup Guide

This guide covers installing dependencies and building whisper.cpp for Phase 2 audio input.

## Prerequisites

Raspberry Pi 5 (or similar) with:
- 4+ cores
- 4GB+ RAM
- Microphone (USB or Pi Audio HAT)

## Step 1: Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3-pyaudio portaudio19-dev git build-essential cmake
```

## Step 2: Install Python Packages

```bash
pip3 install vosk webrtcvad numpy --break-system-packages
```

Or using the requirements file:

```bash
cd /home/tars/openclaw/extensions/tars-channel
pip3 install -r display/requirements.txt --break-system-packages
```

## Step 3: Build whisper.cpp

```bash
cd /home/tars/openclaw/extensions/tars-channel

# Clone and build whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make -j4  # Use all 4 cores

# Download the base.en model (~141MB)
bash ./models/download-ggml-model.sh base.en
```

This will:
- Build `whisper.cpp/build/bin/whisper-cli`
- Download `whisper.cpp/models/ggml-base.en.bin`

## Step 4: Verify Setup

Run the test script:

```bash
cd /home/tars/openclaw/extensions/tars-channel
python3 test_audio.py
```

You should see:
```
✅ All audio components ready!
```

## Models Included in Repo

The Vosk wake word model is already included:
- `display/models/vosk-model-small/` (40MB, committed to repo)

Whisper.cpp and its model are built locally (not in repo):
- `whisper.cpp/` (excluded via .gitignore)

## Testing

### Test Audio Devices

```bash
python3 -c "import pyaudio; p = pyaudio.PyAudio(); print(f'{p.get_device_count()} devices found')"
```

### Test Whisper

```bash
# Record a test file
arecord -d 5 -f S16_LE -r 16000 test.wav

# Transcribe it
./whisper.cpp/build/bin/whisper-cli -m whisper.cpp/models/ggml-base.en.bin -f test.wav
```

### Test the Display

```bash
python3 display/tars_display.py
```

Then:
1. Say "Hey TARS"
2. Speak your message
3. Pause for 1.5 seconds
4. Watch it transcribe and send to OpenClaw

## Troubleshooting

### "No module named 'vosk'"

```bash
pip3 install vosk --break-system-packages
```

### "Whisper binary not found"

Make sure you built whisper.cpp:

```bash
cd whisper.cpp
make -j4
ls -lh build/bin/whisper-cli
```

### "No audio devices found"

Check if PulseAudio is running:

```bash
pactl info
```

Test microphone:

```bash
arecord -l
```

### Wake word not detecting

- Check microphone is working: `arecord -d 3 test.wav && aplay test.wav`
- Try speaking louder or closer to mic
- Adjust `WAKE_WORD_THRESHOLD` in `display/audio_config.py`

### VAD not stopping

- Increase `PAUSE_THRESHOLD` in `display/audio_config.py` (default: 1.5s)
- Try speaking with clearer pauses

### Whisper too slow

- Use `tiny.en` model instead of `base.en` (faster but less accurate):
  ```bash
  cd whisper.cpp
  bash ./models/download-ggml-model.sh tiny.en
  ```
  
  Then update `display/audio_config.py`:
  ```python
  WHISPER_MODEL = "tiny.en"
  WHISPER_MODEL_PATH = "../whisper.cpp/models/ggml-tiny.en.bin"
  ```

## Performance Tuning

### Adjust Audio Config

Edit `display/audio_config.py`:

```python
# Make wake word more/less sensitive
WAKE_WORD_THRESHOLD = 0.7  # Lower = more sensitive

# Change pause detection time
PAUSE_THRESHOLD = 1.5  # Seconds of silence

# Adjust VAD aggressiveness
VAD_MODE = 3  # 0 (least) to 3 (most aggressive)
```

### Test Different Whisper Models

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| tiny.en | 75MB | ~1-2s | Good |
| base.en | 141MB | ~3-4s | Better |
| small.en | 466MB | ~8-10s | Best |

## Next Steps

- Test with real voice input
- Tune thresholds for your environment
- Proceed to Phase 3: Audio output (TTS)
