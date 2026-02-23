#!/usr/bin/env python3
"""Send an INPUT message to OpenClaw to trigger a reply"""
import socket
import json
import time

SOCKET_PATH = "/tmp/tars-channel.sock"

print("Sending input to OpenClaw...")
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect(SOCKET_PATH)

# Send as INPUT (from display to OpenClaw)
msg = json.dumps({
    "type": "input",
    "text": "Hey TARS, this is a test message from the display. Please reply!",
    "timestamp": int(time.time() * 1000)
}) + "\n"

sock.send(msg.encode('utf-8'))
print("✓ Input sent to OpenClaw")
print("OpenClaw should process this and send a reply back through the channel...")

sock.close()
