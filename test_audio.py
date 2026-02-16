#!/usr/bin/env python3
"""Test audio components"""

import sys

print("Testing audio components...")
print()

# Test 1: PyAudio
print("[1/4] Testing PyAudio...")
try:
    import pyaudio
    p = pyaudio.PyAudio()
    print(f"  ✓ PyAudio loaded")
    print(f"  ✓ Found {p.get_device_count()} audio devices")
    
    # List devices
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"    - Input device {i}: {info['name']}")
    
    p.terminate()
except Exception as e:
    print(f"  ✗ PyAudio error: {e}")
    sys.exit(1)

print()

# Test 2: Vosk
print("[2/4] Testing Vosk...")
try:
    from vosk import Model
    import os
    
    model_path = "display/models/vosk-model-small"
    if os.path.exists(model_path):
        print(f"  ✓ Model found: {model_path}")
        # Don't actually load it yet (takes time)
    else:
        print(f"  ✗ Model not found: {model_path}")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ Vosk error: {e}")
    sys.exit(1)

print()

# Test 3: webrtcvad
print("[3/4] Testing webrtcvad...")
try:
    import webrtcvad
    vad = webrtcvad.Vad(3)
    print("  ✓ webrtcvad loaded and initialized")
except Exception as e:
    print(f"  ✗ webrtcvad error: {e}")
    sys.exit(1)

print()

# Test 4: Whisper.cpp
print("[4/4] Testing whisper.cpp...")
try:
    import os
    import subprocess
    
    whisper_bin = "whisper.cpp/build/bin/whisper-cli"
    model_path = "whisper.cpp/models/ggml-base.en.bin"
    
    if os.path.exists(whisper_bin):
        print(f"  ✓ Whisper binary found: {whisper_bin}")
    else:
        print(f"  ✗ Whisper binary not found: {whisper_bin}")
        sys.exit(1)
    
    if os.path.exists(model_path):
        print(f"  ✓ Whisper model found: {model_path}")
    else:
        print(f"  ✗ Whisper model not found: {model_path}")
        sys.exit(1)
    
    # Test execution
    result = subprocess.run([whisper_bin, "--help"], capture_output=True, timeout=5)
    if result.returncode == 0:
        print("  ✓ Whisper executable runs successfully")
    else:
        print(f"  ✗ Whisper failed with code {result.returncode}")
        sys.exit(1)
        
except Exception as e:
    print(f"  ✗ Whisper error: {e}")
    sys.exit(1)

print()
print("✅ All audio components ready!")
print()
print("Next steps:")
print("  1. Test the display: python3 display/tars_display.py")
print("  2. Say 'Hey TARS' to activate voice input")
print("  3. Speak your message (pause for 1.5s to finish)")
