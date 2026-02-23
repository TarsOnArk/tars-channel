#!/usr/bin/env python3
"""
Fake socket server that mimics OpenClaw's tars-channel server.
Accepts display connections and sends test messages to them.
"""
import socket
import json
import time
import os

SOCKET_PATH = "/tmp/tars-test-display.sock"

# Clean up old socket
if os.path.exists(SOCKET_PATH):
    os.unlink(SOCKET_PATH)

server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind(SOCKET_PATH)
server.listen(1)
os.chmod(SOCKET_PATH, 0o666)

print(f"[Test Server] Listening on {SOCKET_PATH}")
print(f"[Test Server] Waiting for display to connect...")

conn, _ = server.accept()
print(f"[Test Server] Display connected!")

time.sleep(1)

messages = [
    "Hello from test server! 🤖",
    "This is message 2 - testing line wrapping with a longer message that should wrap around the screen nicely.",
    "Message 3 - if you see this, the display GUI works!",
    "Final message - the display rendering is confirmed working ✅",
]

for i, text in enumerate(messages):
    msg = json.dumps({
        "type": "message",
        "text": text,
        "timestamp": int(time.time() * 1000)
    }) + "\n"
    
    conn.send(msg.encode('utf-8'))
    print(f"[Test Server] Sent message {i+1}: {text[:50]}...")
    time.sleep(2)

print()
print("[Test Server] All messages sent! Keeping connection open for 10s...")
time.sleep(10)

conn.close()
server.close()
os.unlink(SOCKET_PATH)
print("[Test Server] Done.")
