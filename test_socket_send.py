#!/usr/bin/env python3
"""Test sending messages to the TARS display via socket"""

import socket
import json
import time
import sys

SOCKET_PATH = "/tmp/tars-channel.sock"

def send_message(text):
    """Send a message to the display"""
    try:
        # Connect to socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(SOCKET_PATH)
        print(f"✓ Connected to {SOCKET_PATH}")
        
        # Format message
        msg = json.dumps({
            "type": "message",
            "text": text,
            "timestamp": int(time.time() * 1000)
        }) + "\n"
        
        # Send
        sock.send(msg.encode('utf-8'))
        print(f"✓ Sent: {text}")
        
        sock.close()
        return True
        
    except FileNotFoundError:
        print(f"✗ Socket not found: {SOCKET_PATH}")
        return False
    except ConnectionRefusedError:
        print(f"✗ Connection refused - display not running?")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    # Test messages
    messages = [
        "TARS: Hello! This is a test message.",
        "TARS: Testing 1... 2... 3...",
        "TARS: If you can see this, the display is working! 🎉"
    ]
    
    print("Testing TARS display socket communication")
    print("=" * 60)
    print()
    
    for msg in messages:
        if send_message(msg):
            print(f"Sleeping 2 seconds...")
            time.sleep(2)
        else:
            sys.exit(1)
    
    print()
    print("=" * 60)
    print("Test complete! Check the display for messages.")
