#!/usr/bin/env python3
"""Simple test for wake word detection"""

import sys
import json
import pyaudio
from vosk import Model, KaldiRecognizer

# Add display directory to path for config
sys.path.insert(0, 'display')
import audio_config as cfg

print("=" * 60)
print("Wake Word Detection Test")
print("=" * 60)
print(f"Wake phrase: '{cfg.WAKE_PHRASE}'")
print(f"Model path: {cfg.VOSK_MODEL_PATH}")
print()

# Load Vosk model
print("Loading Vosk model...")
try:
    model = Model(cfg.VOSK_MODEL_PATH)
    print("✓ Model loaded successfully")
except Exception as e:
    print(f"✗ Failed to load model: {e}")
    sys.exit(1)

# Set up recognizer
recognizer = KaldiRecognizer(model, cfg.SAMPLE_RATE)
recognizer.SetWords(True)

# Set up audio
print("\nInitializing microphone...")
try:
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=cfg.CHANNELS,
        rate=cfg.SAMPLE_RATE,
        input=True,
        frames_per_buffer=cfg.CHUNK_SIZE
    )
    print("✓ Microphone ready")
except Exception as e:
    print(f"✗ Failed to open microphone: {e}")
    sys.exit(1)

print()
print("=" * 60)
print(f"🎤 Listening for '{cfg.WAKE_PHRASE}'...")
print("Speak clearly into the microphone.")
print("Press Ctrl+C to stop.")
print("=" * 60)
print()

try:
    while True:
        # Read audio chunk
        data = stream.read(cfg.CHUNK_SIZE, exception_on_overflow=False)
        
        # Process with Vosk
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get('text', '').lower()
            
            if text:
                print(f"Recognized: '{text}'")
                
                # Check for wake phrase
                if cfg.WAKE_PHRASE in text:
                    print()
                    print("=" * 60)
                    print("🎯 WAKE WORD DETECTED!")
                    print("=" * 60)
                    print()
        else:
            # Partial result (ongoing speech)
            partial = json.loads(recognizer.PartialResult())
            partial_text = partial.get('partial', '')
            if partial_text:
                # Show partial transcription (overwrite line)
                print(f"\rPartial: '{partial_text}'", end='', flush=True)

except KeyboardInterrupt:
    print("\n\nStopped by user")
except Exception as e:
    print(f"\n\nError: {e}")
finally:
    # Clean up
    stream.stop_stream()
    stream.close()
    audio.terminate()
    print("\nTest complete.")
