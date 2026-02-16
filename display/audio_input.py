"""Audio input with VAD and Whisper transcription."""

import os
import wave
import subprocess
import pyaudio
import webrtcvad
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
import audio_config as cfg


class AudioRecorder(QThread):
    """Record audio with voice activity detection."""
    
    # Signals
    audio_level = pyqtSignal(float)  # Amplitude for visualizer
    transcription_ready = pyqtSignal(str)  # Final transcription
    error = pyqtSignal(str)
    recording_stopped = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.recording = False
        self.audio = None
        self.stream = None
        self.vad = None
        self.audio_buffer = []
        
    def initialize(self):
        """Initialize audio stream and VAD."""
        try:
            # Initialize VAD
            self.vad = webrtcvad.Vad(cfg.VAD_MODE)
            
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
            self.error.emit(f"Failed to initialize audio recorder: {e}")
            return False
    
    def run(self):
        """Main recording loop with VAD."""
        if not self.initialize():
            return
        
        self.recording = True
        self.audio_buffer = []
        
        silent_frames = 0
        speech_frames = 0
        in_speech = False
        
        max_frames = int(cfg.MAX_RECORDING_SECONDS * cfg.SAMPLE_RATE / cfg.CHUNK_SIZE)
        frame_count = 0
        
        while self.recording and frame_count < max_frames:
            try:
                # Read audio chunk
                data = self.stream.read(cfg.CHUNK_SIZE, exception_on_overflow=False)
                frame_count += 1
                
                # Calculate amplitude for visualizer
                audio_data = np.frombuffer(data, dtype=np.int16)
                amplitude = np.abs(audio_data).mean() / 32768.0  # Normalize to 0-1
                self.audio_level.emit(amplitude)
                
                # Voice activity detection
                is_speech = self.vad.is_speech(data, cfg.SAMPLE_RATE)
                
                if is_speech:
                    speech_frames += 1
                    silent_frames = 0
                    
                    # Start recording after enough speech frames
                    if not in_speech and speech_frames >= cfg.SPEECH_START_FRAMES:
                        in_speech = True
                        print("[AudioInput] Speech started")
                    
                    if in_speech:
                        self.audio_buffer.append(data)
                else:
                    speech_frames = 0
                    
                    if in_speech:
                        silent_frames += 1
                        self.audio_buffer.append(data)  # Keep recording during pauses
                        
                        # Check for pause threshold
                        pause_frames = int(cfg.PAUSE_THRESHOLD * cfg.SAMPLE_RATE / cfg.CHUNK_SIZE)
                        if silent_frames >= pause_frames:
                            print(f"[AudioInput] Pause detected after {len(self.audio_buffer)} frames")
                            break
                
            except Exception as e:
                if self.recording:
                    self.error.emit(f"Recording error: {e}")
                break
        
        # Stop recording
        self.recording = False
        self.cleanup_stream()
        
        # Process the audio
        if self.audio_buffer:
            self.process_audio()
        else:
            self.error.emit("No speech detected")
        
        self.recording_stopped.emit()
    
    def process_audio(self):
        """Save audio to file and transcribe with Whisper."""
        try:
            # Save audio buffer to WAV file
            print(f"[AudioInput] Saving {len(self.audio_buffer)} frames to {cfg.TEMP_AUDIO_PATH}")
            
            with wave.open(cfg.TEMP_AUDIO_PATH, 'wb') as wf:
                wf.setnchannels(cfg.CHANNELS)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(cfg.SAMPLE_RATE)
                wf.writeframes(b''.join(self.audio_buffer))
            
            # Transcribe with Whisper
            text = self.transcribe_whisper()
            
            if text:
                self.transcription_ready.emit(text)
            else:
                self.error.emit("Transcription failed")
                
        except Exception as e:
            self.error.emit(f"Audio processing error: {e}")
    
    def transcribe_whisper(self):
        """Run whisper.cpp to transcribe audio file."""
        try:
            whisper_bin = os.path.expanduser(cfg.WHISPER_PATH)
            model_path = os.path.expanduser(cfg.WHISPER_MODEL_PATH)
            
            if not os.path.exists(whisper_bin):
                raise FileNotFoundError(f"Whisper binary not found: {whisper_bin}")
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Whisper model not found: {model_path}")
            
            print(f"[AudioInput] Transcribing with Whisper...")
            
            # Run whisper.cpp
            result = subprocess.run(
                [whisper_bin, '-m', model_path, '-f', cfg.TEMP_AUDIO_PATH, '-nt'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"[AudioInput] Whisper error: {result.stderr}")
                return None
            
            # Parse output - whisper.cpp outputs "[BLANK_AUDIO]" for silence
            output = result.stdout.strip()
            
            # Extract text (whisper outputs timestamp + text)
            lines = [line.strip() for line in output.split('\n') if line.strip()]
            text_lines = [line for line in lines if not line.startswith('[')]
            
            if not text_lines:
                print("[AudioInput] No transcription found")
                return None
            
            text = ' '.join(text_lines).strip()
            print(f"[AudioInput] Transcribed: {text}")
            
            return text if text and text != "[BLANK_AUDIO]" else None
            
        except subprocess.TimeoutExpired:
            print("[AudioInput] Whisper timeout")
            return None
        except Exception as e:
            print(f"[AudioInput] Whisper error: {e}")
            return None
    
    def stop_recording(self):
        """Stop the recording."""
        self.recording = False
    
    def cleanup_stream(self):
        """Clean up audio stream."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.audio:
            self.audio.terminate()
