#!/bin/bash
# Test all possible WM8960 input configurations to find working mic

CARD=2

echo "Testing all WM8960 input configurations..."
echo "Speak during each 2-second test!"
echo "=========================================="
echo ""

# Function to test recording
test_recording() {
    local name="$1"
    echo "Testing: $name"
    arecord -D pulse -d 2 -f S16_LE -r 16000 -c 1 /tmp/test_$name.wav 2>/dev/null
    python3 -c "
import wave, numpy as np
with wave.open('/tmp/test_$name.wav', 'rb') as wf:
    audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
    max_val = np.abs(audio).max()
    mean_val = np.abs(audio).mean()
    print(f'  Max: {max_val:5d} ({max_val/32768*100:5.1f}%)  Mean: {mean_val:6.1f} ({mean_val/32768*100:6.3f}%)')
    if max_val > 1000:
        print('  ✓✓✓ MICROPHONE WORKS! ✓✓✓')
        exit(1)
"    
    if [ $? -eq 1 ]; then
        echo ""
        echo "Found working configuration: $name"
        return 0
    fi
    return 1
}

# Reset everything first
amixer -c $CARD set 'Left Boost Mixer LINPUT1' off 2>/dev/null
amixer -c $CARD set 'Left Boost Mixer LINPUT2' off 2>/dev/null
amixer -c $CARD set 'Left Boost Mixer LINPUT3' off 2>/dev/null
amixer -c $CARD set 'Right Boost Mixer RINPUT1' off 2>/dev/null
amixer -c $CARD set 'Right Boost Mixer RINPUT2' off 2>/dev/null
amixer -c $CARD set 'Right Boost Mixer RINPUT3' off 2>/dev/null

# Set boost volumes
amixer -c $CARD set 'Left Input Boost Mixer LINPUT1' 3 2>/dev/null
amixer -c $CARD set 'Right Input Boost Mixer RINPUT1' 3 2>/dev/null
amixer -c $CARD set 'Left Input Boost Mixer LINPUT2' 7 2>/dev/null
amixer -c $CARD set 'Right Input Boost Mixer RINPUT2' 7 2>/dev/null
amixer -c $CARD set 'Left Input Boost Mixer LINPUT3' 7 2>/dev/null
amixer -c $CARD set 'Right Input Boost Mixer RINPUT3' 7 2>/dev/null

# Set capture volume high
amixer -c $CARD set Capture 63 cap 2>/dev/null
amixer -c $CARD set 'ADC PCM' 255 2>/dev/null

echo ""
echo "Test 1: LINPUT1/RINPUT1 (typical for onboard mic)"
amixer -c $CARD set 'Left Boost Mixer LINPUT1' on 2>/dev/null
amixer -c $CARD set 'Right Boost Mixer RINPUT1' on 2>/dev/null
test_recording "input1" && exit 0

echo ""
echo "Test 2: LINPUT2/RINPUT2"
amixer -c $CARD set 'Left Boost Mixer LINPUT1' off 2>/dev/null
amixer -c $CARD set 'Right Boost Mixer RINPUT1' off 2>/dev/null
amixer -c $CARD set 'Left Boost Mixer LINPUT2' on 2>/dev/null
amixer -c $CARD set 'Right Boost Mixer RINPUT2' on 2>/dev/null
test_recording "input2" && exit 0

echo ""
echo "Test 3: LINPUT3/RINPUT3"
amixer -c $CARD set 'Left Boost Mixer LINPUT2' off 2>/dev/null
amixer -c $CARD set 'Right Boost Mixer RINPUT2' off 2>/dev/null
amixer -c $CARD set 'Left Boost Mixer LINPUT3' on 2>/dev/null
amixer -c $CARD set 'Right Boost Mixer RINPUT3' on 2>/dev/null
test_recording "input3" && exit 0

echo ""
echo "Test 4: All inputs combined"
amixer -c $CARD set 'Left Boost Mixer LINPUT1' on 2>/dev/null
amixer -c $CARD set 'Left Boost Mixer LINPUT2' on 2>/dev/null
amixer -c $CARD set 'Left Boost Mixer LINPUT3' on 2>/dev/null
amixer -c $CARD set 'Right Boost Mixer RINPUT1' on 2>/dev/null
amixer -c $CARD set 'Right Boost Mixer RINPUT2' on 2>/dev/null
amixer -c $CARD set 'Right Boost Mixer RINPUT3' on 2>/dev/null
test_recording "all_inputs" && exit 0

echo ""
echo "=========================================="
echo "No working microphone input found!"
echo "This suggests:"
echo "  1. No physical microphone is connected"
echo "  2. Microphone requires external power/bias"
echo "  3. GPIO pin needs to be enabled"
echo "  4. Different hardware than expected"
