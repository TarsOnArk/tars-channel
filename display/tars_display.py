#!/usr/bin/env python3
"""
TARS Display - Native PyQt5 interface for TARS embodiment
"""
import sys
import socket
import os
import json
import time
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QLineEdit,
    QVBoxLayout, QWidget, QLabel
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QTextCursor


class SocketListener(QThread):
    """Background thread to listen for messages from OpenClaw"""
    message_received = pyqtSignal(str)
    connected = pyqtSignal(bool)
    
    def __init__(self, socket_path):
        super().__init__()
        self.socket_path = socket_path
        self.running = True
        self.sock = None
        
    def run(self):
        """Connect to Unix socket and listen for messages"""
        while self.running:
            try:
                # Connect to OpenClaw's Unix socket
                self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.sock.connect(self.socket_path)
                print(f"[TARS Display] Connected to {self.socket_path}")
                self.connected.emit(True)
                
                buffer = ""
                while self.running:
                    data = self.sock.recv(4096)
                    if not data:
                        break
                        
                    buffer += data.decode('utf-8')
                    
                    # Process complete JSON messages (newline-delimited)
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            try:
                                msg = json.loads(line)
                                if msg.get('type') == 'message':
                                    self.message_received.emit(msg.get('text', ''))
                            except json.JSONDecodeError:
                                print(f"[TARS Display] Invalid JSON: {line}")
                
                self.sock.close()
                self.sock = None
                self.connected.emit(False)
                print("[TARS Display] Connection closed, retrying...")
                
            except FileNotFoundError:
                print(f"[TARS Display] Socket not found: {self.socket_path}")
                self.connected.emit(False)
                QThread.sleep(2)
            except ConnectionRefusedError:
                print(f"[TARS Display] Connection refused, retrying...")
                self.connected.emit(False)
                QThread.sleep(2)
            except Exception as e:
                print(f"[TARS Display] Error: {e}")
                self.connected.emit(False)
                QThread.sleep(2)
    
    def send_message(self, text):
        """Send a message to OpenClaw"""
        if self.sock:
            try:
                msg = json.dumps({
                    "type": "input",
                    "text": text,
                    "timestamp": int(time.time() * 1000)
                }) + "\n"
                self.sock.send(msg.encode('utf-8'))
                return True
            except Exception as e:
                print(f"[TARS Display] Failed to send message: {e}")
                return False
        return False
    
    def stop(self):
        """Stop the listener thread"""
        self.running = False


class TarsDisplay(QMainWindow):
    """Main TARS display window"""
    
    def __init__(self, socket_path):
        super().__init__()
        self.socket_path = socket_path
        self.init_ui()
        self.init_socket()
        
    def init_ui(self):
        """Initialize the user interface"""
        # Window setup
        self.setWindowTitle("TARS")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Text display area
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFrameStyle(0)  # No frame
        
        # TARS aesthetic styling
        palette = QPalette()
        palette.setColor(QPalette.Base, QColor("#0a0e14"))  # Dark background
        palette.setColor(QPalette.Text, QColor("#00ff41"))  # Green text
        self.text_display.setPalette(palette)
        
        # Monospace font
        font = QFont("Courier New", 14)
        font.setStyleHint(QFont.Monospace)
        self.text_display.setFont(font)
        
        # Input area
        self.input_line = QLineEdit()
        self.input_line.setFrame(False)
        self.input_line.setFont(font)
        self.input_line.setStyleSheet("""
            QLineEdit {
                background-color: #0a0e14;
                color: #00ff41;
                border: 2px solid #00ff41;
                padding: 8px;
            }
        """)
        self.input_line.setPlaceholderText("Type message...")
        self.input_line.returnPressed.connect(self.send_input)
        
        # Hide cursor over display area, show over input
        self.text_display.setCursor(Qt.BlankCursor)
        
        layout.addWidget(self.text_display, stretch=1)
        layout.addWidget(self.input_line)
        
        # Display boot message
        self.append_message("=" * 60)
        self.append_message("TARS SYSTEMS ONLINE")
        self.append_message("Awaiting connection to OpenClaw...")
        self.append_message("=" * 60)
        self.append_message("")
        
    def init_socket(self):
        """Initialize socket listener"""
        self.socket_thread = SocketListener(self.socket_path)
        self.socket_thread.message_received.connect(self.append_message)
        self.socket_thread.connected.connect(self.on_connection_changed)
        self.socket_thread.start()
    
    def on_connection_changed(self, connected):
        """Handle connection status changes"""
        if connected:
            self.append_message("[TARS] Connected to OpenClaw")
            self.input_line.setEnabled(True)
            self.input_line.setFocus()
        else:
            self.append_message("[TARS] Disconnected from OpenClaw")
            self.input_line.setEnabled(False)
    
    def send_input(self):
        """Send user input to OpenClaw"""
        text = self.input_line.text().strip()
        if text:
            # Display user's message locally
            self.append_message(f"> {text}")
            
            # Send to OpenClaw
            if self.socket_thread.send_message(text):
                self.input_line.clear()
            else:
                self.append_message("[TARS] Failed to send message")
        
    def append_message(self, text):
        """Append a message to the display"""
        self.text_display.append(text)
        
        # Auto-scroll to bottom
        cursor = self.text_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_display.setTextCursor(cursor)
        
    def keyPressEvent(self, event):
        """Handle key press events"""
        # Allow Ctrl+C or Escape to quit
        if event.key() == Qt.Key_Escape or \
           (event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier):
            self.close()
            
    def closeEvent(self, event):
        """Clean up when closing"""
        if hasattr(self, 'socket_thread'):
            self.socket_thread.stop()
            self.socket_thread.wait()
        event.accept()


def main():
    """Main entry point"""
    # Socket path (same as OpenClaw will create)
    socket_path = "/tmp/tars-channel.sock"
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create and show display
    display = TarsDisplay(socket_path)
    display.show()
    
    # Run
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
