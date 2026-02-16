#!/bin/bash
# Run TARS display with correct Wayland environment

cd "$(dirname "$0")"

# Wayland environment for Raspberry Pi OS
export QT_QPA_PLATFORM=wayland
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/run/user/1000

python3 display/tars_display.py
