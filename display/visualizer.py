"""Smooth waveform audio visualizer for TARS display.

Draws a flowing sine-wave style visualization with glow effects
using only QPainter — no external dependencies needed.
"""

import math
from collections import deque
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QPainterPath,
    QLinearGradient, QRadialGradient
)
import audio_config as cfg


class AudioVisualizer(QWidget):
    """Smooth flowing waveform visualizer with glow effect."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Audio level history
        self.levels = deque(maxlen=cfg.VIS_HISTORY)
        for _ in range(cfg.VIS_HISTORY):
            self.levels.append(0.0)

        # Animation phase (scrolls the wave)
        self.phase = 0.0

        # Colors
        self.bg_color = QColor("#0a0e14")
        self.primary = QColor(cfg.VIS_COLOR)  # #00ff41
        self.glow_color = QColor(cfg.VIS_COLOR)
        self.glow_color.setAlpha(40)
        self.dim_color = QColor(cfg.VIS_COLOR)
        self.dim_color.setAlpha(100)

        # Update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)

        # Styling
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), self.bg_color)
        self.setPalette(palette)

    def start(self):
        """Start the visualizer animation."""
        update_interval = int(1000 / cfg.VIS_FPS)
        self.timer.start(update_interval)

    def stop(self):
        """Stop the visualizer and reset."""
        self.timer.stop()
        self.levels.clear()
        for _ in range(cfg.VIS_HISTORY):
            self.levels.append(0.0)
        self.phase = 0.0
        self.update()

    def add_level(self, level):
        """Add a new audio level (0.0 - 1.0)."""
        self.levels.append(min(1.0, max(0.0, level)))

    def _tick(self):
        """Advance animation phase and repaint."""
        self.phase += 0.08
        self.update()

    def _build_wave(self, width, height, center_y, amplitude_scale, freq_mult, phase_offset):
        """Build a smooth sine-wave path modulated by audio levels."""
        path = QPainterPath()
        num_points = width
        levels_list = list(self.levels)
        num_levels = len(levels_list)

        for x in range(num_points):
            # Map x position to a level index
            li = int(x / width * num_levels)
            li = min(li, num_levels - 1)
            level = levels_list[li]

            # Base amplitude from audio level, with a small idle wobble
            amp = (level * 0.85 + 0.02) * (height * 0.4) * amplitude_scale

            # Sine wave
            y = center_y + amp * math.sin(
                (x / width) * math.pi * freq_mult + self.phase + phase_offset
            )

            if x == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        return path

    def paintEvent(self, event):
        """Draw layered glowing waveforms."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cy = h / 2.0

        # Background
        painter.fillRect(self.rect(), self.bg_color)

        # Draw a subtle center line
        center_pen = QPen(QColor(cfg.VIS_COLOR))
        center_pen.setWidth(1)
        center_pen_color = QColor(cfg.VIS_COLOR)
        center_pen_color.setAlpha(30)
        center_pen.setColor(center_pen_color)
        painter.setPen(center_pen)
        painter.drawLine(0, int(cy), w, int(cy))

        # Layer 1: Wide glow (blurred effect via thick translucent line)
        glow_path = self._build_wave(w, h, cy, 1.0, 4.0, 0)
        glow_pen = QPen(self.glow_color)
        glow_pen.setWidth(12)
        glow_pen.setCapStyle(Qt.RoundCap)
        glow_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(glow_pen)
        painter.drawPath(glow_path)

        # Layer 2: Medium glow
        med_pen = QPen(self.dim_color)
        med_pen.setWidth(4)
        med_pen.setCapStyle(Qt.RoundCap)
        med_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(med_pen)
        painter.drawPath(glow_path)

        # Layer 3: Sharp primary line
        sharp_pen = QPen(self.primary)
        sharp_pen.setWidth(2)
        sharp_pen.setCapStyle(Qt.RoundCap)
        sharp_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(sharp_pen)
        painter.drawPath(glow_path)

        # Layer 4: Secondary harmonic (subtle)
        harmonic = self._build_wave(w, h, cy, 0.5, 7.0, 1.5)
        harm_pen = QPen(QColor(cfg.VIS_COLOR))
        harm_color = QColor(cfg.VIS_COLOR)
        harm_color.setAlpha(50)
        harm_pen.setColor(harm_color)
        harm_pen.setWidth(1)
        painter.setPen(harm_pen)
        painter.drawPath(harmonic)

        painter.end()
