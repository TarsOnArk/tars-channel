"""Wake word detection using Vosk."""

import json
import os
import pyaudio
from vosk import Model, KaldiRecognizer
from PyQt5.QtCore import QThread, pyqtSignal
import audio_config as cfg


class WakeWordDetector(QThread):
    """Background thread for continuous wake word detection."""
    
    wake_word_detected = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.model = None
        self.recognizer = None
        self.audio = None
        self.stream = None
        
    def initialize(self):
        """Initialize Vosk model and audio stream."""
        try:
            # Check if model exists
            if not os.path.exists(cfg.VOSK_MODEL_PATH):
                raise FileNotFoundError(
                    f"Vosk model not found at {cfg.VOSK_MODEL_PATH}. "
                    "Please download it first."
                )
            
            # Load Vosk model
            self.model = Model(cfg.VOSK_MODEL_PATH)
            self.recognizer = KaldiRecognizer(self.model, cfg.SAMPLE_RATE)
            
            # Set up audio stream
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=cfg.CHANNELS,
                rate=cfg.SAMPLE_RATE,
                input=True,
                frames_per_buffer=cfg.CHUNK_SIZE
            )
            
            return True
            
        except Exception as e:
            self.error.emit(f"Failed to initialize wake word detector: {e}")
            return False
    
    def run(self):
        """Main loop - continuously listen for wake word."""
        if not self.initialize():
            return
        
        self.running = True
        
        while self.running:
            try:
                # Read audio chunk
                data = self.stream.read(cfg.CHUNK_SIZE, exception_on_overflow=False)
                
                # Process with Vosk
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').lower()
                    
                    # Check for wake phrase
                    if cfg.WAKE_PHRASE in text:
                        print(f"[WakeWord] Detected: {text}")
                        self.wake_word_detected.emit()
                        
            except Exception as e:
                if self.running:  # Only emit error if not shutting down
                    self.error.emit(f"Wake word detection error: {e}")
                break
    
    def stop(self):
        """Stop the wake word detector."""
        self.running = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.audio:
            self.audio.terminate()
        
        self.wait()  # Wait for thread to finish
