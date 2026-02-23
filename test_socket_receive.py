#!/usr/bin/env python3
"""Simple socket receiver to test if messages are flowing"""
import socket
import json

SOCKET_PATH = "/tmp/tars-channel.sock"

print("Connecting to socket...")
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect(SOCKET_PATH)
print(f"✓ Connected to {SOCKET_PATH}")

buffer = ""
try:
    while True:
        data = sock.recv(4096)
        if not data:
            print("Connection closed by server")
            break
        
        buffer += data.decode('utf-8')
        print(f"Raw data received ({len(data)} bytes): {data[:100]}")
        
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            if line.strip():
                print(f"Complete message: {line}")
                try:
                    msg = json.parse(line)
                    print(f"  Parsed: {msg}")
                except:
                    print(f"  (not JSON)")
except KeyboardInterrupt:
    print("\nStopped")
finally:
    sock.close()
