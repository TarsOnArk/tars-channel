# TARS Channel

Physical embodiment channel for OpenClaw - displays messages on a screen with TARS-inspired interface.

## Overview

TARS Channel provides a native PyQt5 display interface that shows OpenClaw messages on a physical screen (designed for Raspberry Pi with display). Communication happens via Unix domain sockets for maximum performance and low latency.

## Architecture

```
┌─────────────────────────────────┐
│  OpenClaw Gateway (Node.js)     │
│  └── tars-channel extension     │
│      └── Unix Socket Server     │
└──────────────┬──────────────────┘
               │ /tmp/tars-channel.sock
┌──────────────▼──────────────────┐
│  TARS Display (Python/PyQt5)    │
│  └── Fullscreen interface       │
└─────────────────────────────────┘
```

## Features

### Phase 1 (Current) ✅
- ✅ Unix socket communication
- ✅ PyQt5 native display
- ✅ TARS-inspired aesthetic (green on black, monospace)
- ✅ Real-time message display
- ✅ Auto-reconnection
- ✅ Systemd service for auto-start

### Phase 2+ (Planned)
- 🚧 Image display
- 🚧 Audio output (TTS via speakers)
- 🚧 Audio input (microphone)
- 🚧 Animations and effects
- 🚧 Status indicators

## Installation

### Prerequisites
- Raspberry Pi (or Linux system) with display
- Python 3.7+
- OpenClaw installed at `/home/tars/openclaw`

### Install

```bash
cd /home/tars/openclaw/extensions/tars-channel
./install.sh
```

### Enable Auto-Start

```bash
sudo systemctl enable tars-display
sudo systemctl start tars-display
```

### Manual Test

```bash
# Terminal 1: Start OpenClaw gateway
cd /home/tars/openclaw
openclaw gateway start

# Terminal 2: Start display
python3 /home/tars/openclaw/extensions/tars-channel/display/tars_display.py
```

## Configuration

Enable the channel in OpenClaw config:

```yaml
channels:
  tars-channel:
    enabled: true
    port: 3030  # Not used yet, reserved for future
```

## Development

### Project Structure

```
tars-channel/
├── display/
│   ├── tars_display.py       # PyQt5 display app
│   └── requirements.txt      # Python dependencies
├── src/
│   ├── channel.ts            # OpenClaw channel plugin
│   └── server.ts             # Unix socket server
├── systemd/
│   └── tars-display.service  # Systemd service
├── install.sh                # Installation script
└── README.md                 # This file
```

### Key Files

- **`display/tars_display.py`** - Main display application
  - Fullscreen PyQt5 window
  - Unix socket client
  - Message rendering

- **`src/server.ts`** - Socket server
  - Creates `/tmp/tars-channel.sock`
  - Broadcasts messages to connected displays
  - Handles multiple connections

- **`src/channel.ts`** - OpenClaw integration
  - Registers as channel plugin
  - Routes outbound messages to display
  - Lifecycle management

## Usage

Once installed and configured, all messages sent to the `tars-channel` will appear on the physical display.

From OpenClaw, you can send messages via:
```typescript
// Internal routing will handle this automatically
```

Or test with OpenClaw CLI:
```bash
openclaw message send --channel tars-channel --text "Hello, TARS!"
```

## Troubleshooting

### Display won't start
- Check if OpenClaw gateway is running: `openclaw status`
- Check display service: `sudo systemctl status tars-display`
- Check logs: `sudo journalctl -u tars-display -f`

### No connection
- Verify socket exists: `ls -l /tmp/tars-channel.sock`
- Check socket permissions: Should be `srw-rw-rw-`
- Display will retry every 2 seconds automatically

### Display is blank
- Check if messages are being sent
- Verify PyQt5 is installed: `python3 -c "import PyQt5"`

## Exit Display

Press **Escape** or **Ctrl+C** to exit the display app.

## License

Same as OpenClaw
