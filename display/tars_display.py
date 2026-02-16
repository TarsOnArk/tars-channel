#!/usr/bin/env python3
"""
TARS Display - Native PyQt5 interface for TARS embodiment with voice input
"""
import sys
import socket
import os
import json
import time
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QLineEdit,
    QVBoxLayout, QWidget, QLabel, QStackedWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QTextCursor

# Import audio components
try:
    from wake_word import WakeWordDetector
    from audio_input import AudioRecorder
    from visualizer import AudioVisualizer
    AUDIO_AVAILABLE = True
except ImportError as e:
    print(f"[TARS Display] Audio components not available: {e}")
    AUDIO_AVAILABLE = False


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
    """Main TARS display window with voice input"""
    
    # Display states
    STATE_NORMAL = "normal"
    STATE_LISTENING = "listening"
    STATE_PROCESSING = "processing"
    
    def __init__(self, socket_path):
        super().__init__()
        self.socket_path = socket_path
        self.state = self.STATE_NORMAL
        self.init_ui()
        self.init_socket()
        self.init_audio()
        
    def init_ui(self):
        """Initialize the user interface"""
        # Window setup
        self.setWindowTitle("TARS")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()
        
        # Central widget with stacked views
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # Stacked widget to switch between normal and listening views
        self.stack = QStackedWidget()
        
        # === NORMAL VIEW (conversation display) ===
        normal_widget = QWidget()
        normal_layout = QVBoxLayout(normal_widget)
        normal_layout.setContentsMargins(0, 0, 0, 0)
        normal_layout.setSpacing(10)
        
        # Text display area
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFrameStyle(0)
        
        # TARS aesthetic styling
        palette = QPalette()
        palette.setColor(QPalette.Base, QColor("#0a0e14"))
        palette.setColor(QPalette.Text, QColor("#00ff41"))
        self.text_display.setPalette(palette)
        
        # Monospace font
        self.font = QFont("Courier New", 14)
        self.font.setStyleHint(QFont.Monospace)
        self.text_display.setFont(self.font)
        self.text_display.setCursor(Qt.BlankCursor)
        
        normal_layout.addWidget(self.text_display, stretch=1)
        
        # === LISTENING VIEW (audio visualizer) ===
        listening_widget = QWidget()
        listening_layout = QVBoxLayout(listening_widget)
        listening_layout.setContentsMargins(20, 20, 20, 20)
        listening_layout.setSpacing(20)
        
        # Title
        self.listening_title = QLabel("🎤 LISTENING")
        self.listening_title.setFont(QFont("Courier New", 24, QFont.Bold))
        self.listening_title.setStyleSheet("color: #00ff41;")
        self.listening_title.setAlignment(Qt.AlignCenter)
        
        # Separator
        separator = QLabel("═" * 40)
        separator.setFont(self.font)
        separator.setStyleSheet("color: #00ff41;")
        separator.setAlignment(Qt.AlignCenter)
        
        # Visualizer
        if AUDIO_AVAILABLE:
            self.visualizer = AudioVisualizer()
            self.visualizer.setMinimumHeight(200)
        else:
            self.visualizer = QLabel("[Audio visualizer unavailable]")
            self.visualizer.setAlignment(Qt.AlignCenter)
            self.visualizer.setStyleSheet("color: #00ff41;")
        
        # Transcription display
        self.transcription_label = QLabel("")
        self.transcription_label.setFont(self.font)
        self.transcription_label.setStyleSheet("color: #00ff41;")
        self.transcription_label.setAlignment(Qt.AlignCenter)
        self.transcription_label.setWordWrap(True)
        
        # Instruction
        self.instruction_label = QLabel("💬 Speak now (pause to finish)")
        self.instruction_label.setFont(self.font)
        self.instruction_label.setStyleSheet("color: #00ff41;")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        
        listening_layout.addWidget(self.listening_title)
        listening_layout.addWidget(separator)
        listening_layout.addWidget(self.visualizer, stretch=1)
        listening_layout.addWidget(self.transcription_label)
        listening_layout.addWidget(self.instruction_label)
        
        # Add both views to stack
        self.stack.addWidget(normal_widget)  # index 0
        self.stack.addWidget(listening_widget)  # index 1
        
        # Input area
        self.input_line = QLineEdit()
        self.input_line.setFrame(False)
        self.input_line.setFont(self.font)
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
        
        main_layout.addWidget(self.stack, stretch=1)
        main_layout.addWidget(self.input_line)
        
        # Start with normal view
        self.stack.setCurrentIndex(0)
        
        # Display boot message
        self.append_message("=" * 60)
        self.append_message("TARS SYSTEMS ONLINE")
        self.append_message("Awaiting connection to OpenClaw...")
        if AUDIO_AVAILABLE:
            self.append_message("Voice input: Enabled (say 'Hey TARS')")
        else:
            self.append_message("Voice input: Disabled (dependencies missing)")
        self.append_message("=" * 60)
        self.append_message("")
        
    def init_socket(self):
        """Initialize socket listener"""
        self.socket_thread = SocketListener(self.socket_path)
        self.socket_thread.message_received.connect(self.append_message)
        self.socket_thread.connected.connect(self.on_connection_changed)
        self.socket_thread.start()
    
    def init_audio(self):
        """Initialize audio components"""
        if not AUDIO_AVAILABLE:
            return
        
        # Wake word detector
        self.wake_detector = WakeWordDetector()
        self.wake_detector.wake_word_detected.connect(self.on_wake_word)
        self.wake_detector.error.connect(self.on_audio_error)
        
        # Audio recorder
        self.audio_recorder = AudioRecorder()
        self.audio_recorder.audio_level.connect(self.on_audio_level)
        self.audio_recorder.transcription_ready.connect(self.on_transcription)
        self.audio_recorder.error.connect(self.on_audio_error)
        self.audio_recorder.recording_stopped.connect(self.on_recording_stopped)
        
        # Start wake word detection
        self.wake_detector.start()
        self.append_message("[TARS] Listening for 'Hey TARS'...")
    
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
    
    def on_wake_word(self):
        """Handle wake word detection"""
        print("[TARS Display] Wake word detected!")
        self.set_state(self.STATE_LISTENING)
        
        # Start recording
        if hasattr(self, 'audio_recorder'):
            self.audio_recorder.start()
    
    def on_audio_level(self, level):
        """Handle audio level updates for visualizer"""
        if AUDIO_AVAILABLE and hasattr(self, 'visualizer'):
            self.visualizer.add_level(level)
    
    def on_transcription(self, text):
        """Handle transcription ready"""
        print(f"[TARS Display] Transcription: {text}")
        self.set_state(self.STATE_PROCESSING)
        
        # Display transcribed text
        self.append_message(f"> {text} [voice]")
        
        # Send to OpenClaw
        if self.socket_thread.send_message(text):
            pass
        else:
            self.append_message("[TARS] Failed to send message")
        
        # Return to normal view after a brief delay
        QTimer.singleShot(1000, lambda: self.set_state(self.STATE_NORMAL))
    
    def on_recording_stopped(self):
        """Handle recording stopped"""
        print("[TARS Display] Recording stopped")
    
    def on_audio_error(self, error):
        """Handle audio errors"""
        print(f"[TARS Display] Audio error: {error}")
        self.append_message(f"[TARS Audio] {error}")
        self.set_state(self.STATE_NORMAL)
    
    def set_state(self, state):
        """Change display state"""
        if state == self.state:
            return
        
        print(f"[TARS Display] State: {self.state} -> {state}")
        self.state = state
        
        if state == self.STATE_NORMAL:
            # Show conversation view
            self.stack.setCurrentIndex(0)
            if AUDIO_AVAILABLE and hasattr(self, 'visualizer'):
                self.visualizer.stop()
            self.input_line.setEnabled(True)
            
        elif state == self.STATE_LISTENING:
            # Show listening view
            self.stack.setCurrentIndex(1)
            if AUDIO_AVAILABLE and hasattr(self, 'visualizer'):
                self.visualizer.start()
            self.transcription_label.setText("Listening...")
            self.instruction_label.setText("💬 Speak now (pause to finish)")
            self.input_line.setEnabled(False)
            
        elif state == self.STATE_PROCESSING:
            # Update listening view to show processing
            self.stack.setCurrentIndex(1)
            if AUDIO_AVAILABLE and hasattr(self, 'visualizer'):
                self.visualizer.stop()
            self.transcription_label.setText("Processing...")
            self.instruction_label.setText("🤖 Thinking...")
        
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
        
        if AUDIO_AVAILABLE:
            if hasattr(self, 'wake_detector'):
                self.wake_detector.stop()
            if hasattr(self, 'audio_recorder') and self.audio_recorder.isRunning():
                self.audio_recorder.stop_recording()
                self.audio_recorder.wait()
        
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
