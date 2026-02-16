#!/usr/bin/env python3
"""
TARS Display - Native PyQt5 interface for TARS embodiment
"""
import sys
import socket
import os
import json
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QTextCursor


class SocketListener(QThread):
    """Background thread to listen for messages from OpenClaw"""
    message_received = pyqtSignal(str)
    
    def __init__(self, socket_path):
        super().__init__()
        self.socket_path = socket_path
        self.running = True
        
    def run(self):
        """Connect to Unix socket and listen for messages"""
        while self.running:
            try:
                # Connect to OpenClaw's Unix socket
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(self.socket_path)
                print(f"[TARS Display] Connected to {self.socket_path}")
                
                buffer = ""
                while self.running:
                    data = sock.recv(4096)
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
                
                sock.close()
                print("[TARS Display] Connection closed, retrying...")
                
            except FileNotFoundError:
                print(f"[TARS Display] Socket not found: {self.socket_path}")
                QThread.sleep(2)
            except ConnectionRefusedError:
                print(f"[TARS Display] Connection refused, retrying...")
                QThread.sleep(2)
            except Exception as e:
                print(f"[TARS Display] Error: {e}")
                QThread.sleep(2)
    
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
        
        # Hide cursor
        self.setCursor(Qt.BlankCursor)
        
        layout.addWidget(self.text_display)
        
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
        self.socket_thread.start()
        
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
