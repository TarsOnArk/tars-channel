#!/bin/bash
# Dump all mixer controls for WM8960

echo "=== WM8960 Mixer State Dump ==="
echo ""

CARD=2

# Get all simple controls
amixer -c $CARD scontrols | while read line; do
    # Extract control name
    control=$(echo "$line" | sed "s/Simple mixer control '\(.*\)',0/\1/")
    
    # Get the control value
    echo "[$control]"
    amixer -c $CARD sget "$control" 2>/dev/null | grep -v "Simple mixer" | head -5
    echo ""
done
