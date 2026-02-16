# Quick Start: Phase 2 Audio Implementation

## Current Status
✅ **Phase 1 Complete:** Bidirectional text communication (display ↔ OpenClaw)

## What to Build Next
🎤 **Phase 2:** Voice input with wake word detection and local STT

## Key Files
- **Build Plan:** `PHASE2_AUDIO_PLAN.md` (complete architecture & steps)
- **Current Display:** `display/tars_display.py`
- **Socket Server:** `src/server.ts`
- **Memory:** `/home/tars/.openclaw/workspace/memory/2026-02-16.md`

## System Info
- **Hardware:** Raspberry Pi 5, 8GB RAM, 4 cores
- **Location:** lil-ark
- **Repo:** `/home/tars/openclaw/extensions/tars-channel`
- **GitHub:** https://github.com/TarsOnArk/tars-channel

## Architecture Summary
```
Mic → Vosk (wake word) → VAD → whisper.cpp → Socket → OpenClaw
        "Hey TARS"      pause    ~3-4s text
```

## First Steps for Implementation

1. **Install whisper.cpp**
   ```bash
   cd /home/tars/openclaw/extensions/tars-channel
   git clone https://github.com/ggerganov/whisper.cpp
   cd whisper.cpp && make -j4
   bash ./models/download-ggml-model.sh base.en
   ```

2. **Install Python dependencies**
   ```bash
   pip3 install vosk webrtcvad numpy
   sudo apt-get install python3-pyaudio portaudio19-dev
   ```

3. **Download Vosk wake word model**
   ```bash
   cd /home/tars/openclaw/extensions/tars-channel/display
   mkdir -p models
   cd models
   wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
   unzip vosk-model-small-en-us-0.15.zip
   ```

4. **Test microphone**
   ```bash
   arecord -d 3 -f S16_LE -r 16000 test.wav
   aplay test.wav
   ```

5. **Start building** according to `PHASE2_AUDIO_PLAN.md`

## Testing Phase 1 First (Optional)
If you want to test text communication first:
```bash
# Enable plugin
openclaw plugins enable tars-channel
openclaw gateway restart

# Start display
DISPLAY=:0 python3 /home/tars/openclaw/extensions/tars-channel/display/tars_display.py
```

## Phase 2 Goals
- [ ] Wake word detection working
- [ ] Audio visualizer showing waveform
- [ ] VAD detecting speech/pause
- [ ] whisper.cpp transcribing accurately
- [ ] Text sending to OpenClaw via socket
- [ ] UI transitioning between states smoothly

## Context
No keyboard on lil-ark, so voice input is **required** for actual testing of the channel.
