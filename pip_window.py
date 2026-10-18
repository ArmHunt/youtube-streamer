"""Floating Picture-in-Picture window."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QRect, Slot
from PySide6.QtGui import Qt as QtEnum
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QFrame,
    QVBoxLayout,
    QWidget,
)

from player import PlayerEngine

logger = logging.getLogger(__name__)


class PiPWindow(QMainWindow):
    """Small floating always-on-top window for picture-in-picture mode."""

    # Window will be resizable and draggable
    WINDOW_MIN_WIDTH = 320
    WINDOW_MIN_HEIGHT = 240
    BORDER = 12  # px for resize grip

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player: PlayerEngine | None = None
        self._video_label: QLabel | None = None
        self._setup_ui()
        self._configure_window()

    def set_player(self, player: PlayerEngine):
        """Attach the player engine."""
        self._player = player

    def play_video(self, video_id: str, stream_url: str):
        """Load and play a video in the PiP window."""
        self._player.play_video(
            video_id=video_id,
            stream_url=stream_url,
        )
        self.show()
        self.raise_()
        self.activateWindow()

    def pause(self):
        if self._player:
            self._player.pause()

    def play(self):
        if self._player:
            self._player.play()

    def stop(self):
        if self._player:
            self._player.stop()

    # ── UI Construction ──────────────────────────────────────────

    def _setup_ui(self):
        # Central widget with dark background
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Video container
        container = QFrame()
        container.setObjectName("pipContainer")
        container.setStyleSheet("""
            QFrame#pipContainer {
                background-color: #0a0a0a;
                border: none;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Video label (will display video frame or thumbnail)
        self._video_label = QLabel()
        self._video_label.setAlignment(
            Qt.AlignCenter | QtEnum.AlignVCenter
        )
        self._video_label.setStyleSheet("""
            QLabel {
                background-color: #0a0a0a;
                color: #aaa;
                font-size: 14px;
            }
        """)
        container_layout.addWidget(self._video_label, stretch=1)

        layout.addWidget(container, stretch=1)

        # Resize grip in bottom-right corner
        self._resize_grip = QLabel("⤡")
        self._resize_grip.setAlignment(Qt.AlignCenter)
        self._resize_grip.setStyleSheet("""
            QLabel {
                color: #fff;
                font-size: 16px;
                background: rgba(255,255,255,0.1);
            }
            QLabel:hover {
                background: rgba(255,255,255,0.2);
            }
        """)
        self._resize_grip.setCursor(QtEnum.CursorShape.SizeFDiagCursor)
        self._resize_grip.mouseMoveEvent = self._on_resize_move
        self._resize_grip.mousePressEvent = self._on_resize_press
        self._resize_grip.mouseReleaseEvent = self._on_resize_release
        layout.addWidget(self._resize_grip)

    def _configure_window(self):
        """Make window always-on-top, transparent background."""
        self.setWindowFlags(
            QtEnum.WindowType.Window
            | QtEnum.WindowType.FramelessWindowHint
            | QtEnum.WindowType.Tool
            | QtEnum.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(QtEnum.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtEnum.WidgetAttribute.WA_DeleteOnClose, False)
        self.setWindowTitle("YouTube Streamer — PiP")
        self.resize(480, 270)
        self.move(100, 100)

    # ── Drag & Resize ────────────────────────────────────────────

    _resize_drag_start: tuple | None = None

    def _on_resize_press(self, event):
        if event.button() == QtEnum.MouseButton.LeftButton:
            self._resize_drag_start = (event.globalPosition().toPoint(), self.size())
            event.accept()

    def _on_resize_move(self, event):
        if self._resize_drag_start is not None:
            delta = event.globalPosition().toPoint() - self._resize_drag_start[0]
            new_size = self._resize_drag_start[1] + delta
            new_w = max(self.WINDOW_MIN_WIDTH, new_size.width())
            new_h = max(self.WINDOW_MIN_HEIGHT, new_size.height())
            self.resize(new_w, new_h)
            event.accept()

    def _on_resize_release(self, event):
        self._resize_drag_start = None
        event.accept()

    # ── Drag window by title ─────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == QtEnum.MouseButton.LeftButton:
            self._mouse_press_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtEnum.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._mouse_press_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            event.accept()

    def mouseReleaseEvent(self, event):
        event.accept()
