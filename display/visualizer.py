"""Audio visualizer widget for TARS display."""

from collections import deque
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen
import audio_config as cfg


class AudioVisualizer(QWidget):
    """Real-time audio waveform visualizer."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Audio level history (ring buffer)
        self.levels = deque(maxlen=cfg.VIS_HISTORY)
        
        # Initialize with zeros
        for _ in range(cfg.VIS_HISTORY):
            self.levels.append(0.0)
        
        # Colors
        self.bg_color = QColor("#0a0e14")
        self.fg_color = QColor(cfg.VIS_COLOR)
        
        # Update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        
        # Styling
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), self.bg_color)
        self.setPalette(palette)
    
    def start(self):
        """Start the visualizer."""
        update_interval = int(1000 / cfg.VIS_FPS)
        self.timer.start(update_interval)
    
    def stop(self):
        """Stop the visualizer."""
        self.timer.stop()
        # Clear levels
        self.levels.clear()
        for _ in range(cfg.VIS_HISTORY):
            self.levels.append(0.0)
        self.update()
    
    def add_level(self, level):
        """Add a new audio level (0.0 - 1.0)."""
        self.levels.append(level)
    
    def paintEvent(self, event):
        """Draw the waveform."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), self.bg_color)
        
        # Set up pen
        pen = QPen(self.fg_color)
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Get dimensions
        width = self.width()
        height = self.height()
        center_y = height // 2
        
        # Calculate bar width
        num_bars = len(self.levels)
        if num_bars == 0:
            return
        
        bar_width = max(1, width // num_bars)
        spacing = max(0, bar_width // 4)
        
        # Draw bars
        for i, level in enumerate(self.levels):
            x = i * bar_width
            
            # Calculate bar height (symmetric around center)
            bar_height = int(level * center_y * 0.8)  # 80% of half height
            
            # Draw bar
            if bar_height > 0:
                painter.drawRect(
                    x + spacing,
                    center_y - bar_height,
                    bar_width - spacing * 2,
                    bar_height * 2
                )
