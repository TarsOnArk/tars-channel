// Quick test to trigger a message send via the tars-channel
const net = require('net');

const msg = JSON.stringify({
  type: "message",
  text: "🤖 Test from OpenClaw server - can you see this?",
  timestamp: Date.now()
}) + "\n";

// Connect as a client and just disconnect - this should trigger the display connection
const client = net.createConnection('/tmp/tars-channel.sock', () => {
  console.log('Connected to server');
  // Don't send anything, just trigger connection event
  setTimeout(() => client.end(), 100);
});

client.on('error', (err) => console.error('Error:', err));
