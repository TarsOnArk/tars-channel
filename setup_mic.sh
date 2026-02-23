#!/bin/bash
# Setup WM8960 audio codec for microphone input

echo "Setting up WM8960 microphone..."

# Card 2 is the wm8960-soundcard
CARD=2

# Enable capture
amixer -c $CARD set Capture 63 cap

# Set ADC volume
amixer -c $CARD set 'ADC PCM' 195

# Enable input boost (typically LINPUT1/RINPUT1 for onboard mic)
amixer -c $CARD set 'Left Input Boost Mixer LINPUT1' 3
amixer -c $CARD set 'Right Input Boost Mixer RINPUT1' 3

# Alternative: Try LINPUT2/RINPUT2 if external mic
amixer -c $CARD set 'Left Input Boost Mixer LINPUT2' 5
amixer -c $CARD set 'Right Input Boost Mixer RINPUT2' 5

# Disable noise gate (can block quiet speech)
amixer -c $CARD set 'Noise Gate' 0

# Disable ALC (automatic level control) for now
amixer -c $CARD set 'ALC Function' 'Disabled'

# Set input mixer boost
amixer -c $CARD set 'Left Input Mixer Boost' on
amixer -c $CARD set 'Right Input Mixer Boost' on

echo "Done! Testing microphone..."
echo "Recording 3 seconds..."
arecord -D pulse -d 3 -f S16_LE -r 16000 -c 1 /tmp/test_final.wav

echo "Checking audio level..."
python3 -c "
import wave
import numpy as np

with wave.open('/tmp/test_final.wav', 'rb') as wf:
    frames = wf.readframes(wf.getnframes())
    audio = np.frombuffer(frames, dtype=np.int16)
    max_val = np.abs(audio).max()
    mean_val = np.abs(audio).mean()
    print(f'Max: {max_val} ({max_val/32768*100:.1f}%)')
    print(f'Mean: {mean_val:.1f} ({mean_val/32768*100:.3f}%)')
    if max_val > 100:
        print('✓ Microphone is working!')
    else:
        print('✗ Still silent - may need hardware check')
"
