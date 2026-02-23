#!/bin/bash
cd "$(dirname "$0")"

echo "=== Testing full message flow ==="
echo

echo "1. Checking socket status..."
lsof /tmp/tars-channel.sock | head -5

echo
echo "2. Sending test input to OpenClaw..."
python3 test_input_send.py

echo
echo "3. Waiting 5 seconds for OpenClaw to process..."
sleep 5

echo
echo "4. Checking for tars-channel session..."
openclaw sessions list | grep -E "tars|channel" || echo "  → No tars-channel session found"

echo
echo "5. Checking display log for received messages..."
tail -30 /tmp/tars-display-test.log | grep -E "Received|Processing|message" || echo "  → No received messages in display log"

echo
echo "=== Test complete ==="
