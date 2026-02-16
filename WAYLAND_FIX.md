# Wayland Display Fix

## Problem

The TARS display failed to start with this error:
```
qt.qpa.xcb: could not connect to display 
qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
```

## Cause

Raspberry Pi OS (Bookworm) uses **Wayland** with the **labwc** compositor by default, not X11. PyQt5 was trying to use the X11 backend (xcb) which doesn't work on Wayland.

## Solution

Set the Qt platform to Wayland using environment variables:

```bash
export QT_QPA_PLATFORM=wayland
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/run/user/1000
```

## How to Run

### Manual Run (for testing)

```bash
cd /home/tars/openclaw/extensions/tars-channel
./run_display.sh
```

Or directly:
```bash
cd /home/tars/openclaw/extensions/tars-channel
QT_QPA_PLATFORM=wayland WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 python3 display/tars_display.py
```

### Systemd Service

The service file has been updated with the correct environment variables:

```ini
[Service]
Environment=QT_QPA_PLATFORM=wayland
Environment=WAYLAND_DISPLAY=wayland-0
Environment=XDG_RUNTIME_DIR=/run/user/1000
```

Install and start the service:

```bash
cd /home/tars/openclaw/extensions/tars-channel
sudo ./install.sh
sudo systemctl enable --now tars-display.service
```

## Checking Display

To verify the Wayland compositor is running:

```bash
# Check for labwc (Wayland compositor)
ps aux | grep labwc

# Check Wayland socket
ls -la /run/user/1000/wayland-*

# Check if display is running
ps aux | grep tars_display
```

## Troubleshooting

### "No Qt platform plugin could be initialized"

Make sure you're using the Wayland environment variables:
```bash
export QT_QPA_PLATFORM=wayland
```

### Display not showing

1. Check if labwc is running: `ps aux | grep labwc`
2. Check if you're logged into the graphical session
3. Try running from a terminal on the Pi directly (not via SSH)

### "Wayland does not support QWindow::requestActivate()"

This is a harmless warning and can be ignored. It just means Wayland handles window activation differently than X11.

## Notes

- **Raspberry Pi OS Bookworm** (Debian 13) uses Wayland by default
- **PyQt5** supports both X11 and Wayland
- The warning about `requestActivate()` is expected and doesn't affect functionality
- If you need X11 for some reason, you can switch back in `raspi-config`

## Reference

- Wayland compositor: **labwc** (Openbox-style Wayland compositor)
- Wayland socket: `/run/user/1000/wayland-0`
- Qt Wayland platform plugins: `wayland-egl`, `wayland`, `wayland-xcomposite-egl`
