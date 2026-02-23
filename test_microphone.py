#!/usr/bin/env python3
"""Test microphone capture and show audio levels"""

import pyaudio
import numpy as np
import time

print("=" * 60)
print("Microphone Test - Audio Level Monitor")
print("=" * 60)
print()

# List audio devices
print("Available audio devices:")
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f"  [{i}] {info['name']}")
        print(f"      Sample rate: {int(info['defaultSampleRate'])} Hz")
        print(f"      Input channels: {info['maxInputChannels']}")
        print()

# Try to open default input
print("=" * 60)
print("Testing default input device...")
print("Speak into the microphone - you should see the level bars move.")
print("Press Ctrl+C to stop.")
print("=" * 60)
print()

try:
    # Open stream
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024
    )
    
    print("✓ Microphone opened successfully")
    print()
    
    # Monitor audio levels
    while True:
        # Read audio
        data = stream.read(1024, exception_on_overflow=False)
        
        # Convert to numpy array
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        # Calculate level (0-1)
        level = np.abs(audio_data).mean() / 32768.0
        
        # Create visual bar
        bar_length = int(level * 50)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        
        # Print level (overwrite line)
        print(f"\rLevel: [{bar}] {level:.3f}", end='', flush=True)
        
        time.sleep(0.05)
        
except KeyboardInterrupt:
    print("\n\nStopped by user")
except Exception as e:
    print(f"\n✗ Error: {e}")
    print()
    print("Trying to open ALSA hardware device directly...")
    print()
    
    # Try ALSA hardware device
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            input_device_index=None,
            frames_per_buffer=1024
        )
        print("✓ Opened with alternative method")
    except Exception as e2:
        print(f"✗ Also failed: {e2}")
finally:
    if 'stream' in locals():
        stream.stop_stream()
        stream.close()
    p.terminate()
    print("\nTest complete.")
