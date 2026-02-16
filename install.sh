#!/bin/bash
# TARS Channel Installation Script

set -e

echo "=== TARS Channel Installation ==="
echo

# Check if running on lil-ark
if [ "$(hostname)" != "lil-ark" ]; then
    echo "⚠️  Warning: This script is designed for lil-ark"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r display/requirements.txt

# Make display script executable
echo "🔧 Setting permissions..."
chmod +x display/tars_display.py

# Install systemd service
echo "⚙️  Installing systemd service..."
sudo cp systemd/tars-display.service /etc/systemd/system/
sudo systemctl daemon-reload

echo
echo "✅ Installation complete!"
echo
echo "To enable auto-start on boot:"
echo "  sudo systemctl enable tars-display"
echo
echo "To start now:"
echo "  sudo systemctl start tars-display"
echo
echo "To test manually:"
echo "  python3 display/tars_display.py"
echo
echo "Note: Make sure OpenClaw gateway is running first!"
echo "      The display will retry connection every 2 seconds."
