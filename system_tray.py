"""System tray with background audio playback controls."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QSystemTrayIcon,
    QMenu,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
)

from player import PlayerEngine

logger = logging.getLogger(__name__)


class SystemTrayManager:
    """Manages the system tray icon with playback controls."""

    def __init__(self, player: PlayerEngine, parent: QWidget):
        self._player = player
        self._parent = parent
        self._tray: QSystemTrayIcon | None = None
        self._visible = False
        self._setup_tray()
        logger.info("SystemTrayManager initialized")

    @property
    def visible(self) -> bool:
        return self._visible

    @Slot()
    def toggle_visibility(self):
        """Toggle main window visibility from tray."""
        self._visible = not self._visible
        self._parent.show()
        self._parent.raise_()
        self._parent.activateWindow()

    @Slot()
    def play_pause(self):
        if self._player.is_playing():
            self._player.pause()
        else:
            self._player.play()

    @Slot()
    def play(self):
        self._player.play()

    @Slot()
    def pause(self):
        self._player.pause()

    @Slot()
    def stop(self):
        self._player.stop()

    @Slot()
    def next_track(self):
        self._player.next_video()

    @Slot()
    def prev_track(self):
        self._player.prev_video()

    def set_volume(self, value: int):
        self._player.set_volume(value)

    def set_status_text(self, title: str, subtitle: str = ""):
        """Update tray icon tooltip with current track info."""
        if self._tray:
            tooltip = f"{title}\n{subtitle}" if subtitle else title
            self._tray.setToolTip(tooltip)

    # ── Tray setup ───────────────────────────────────────────────

    def _setup_tray(self):
        """Create system tray icon with playback controls."""
        self._tray = QSystemTrayIcon(self._parent)

        # Create menu
        menu = QMenu(self._parent)

        # Status label
        status_action = QAction("YouTube Streamer", self._parent)
        status_action.setEnabled(False)
        menu.addAction(status_action)
        menu.addSeparator()

        # Playback controls
        play_action = QAction("▶ Play", self._parent)
        play_action.triggered.connect(self._tray_play_pause)
        menu.addAction(play_action)

        pause_action = QAction("⏸ Pause", self._parent)
        pause_action.triggered.connect(self._tray_pause)
        menu.addAction(pause_action)

        menu.addSeparator()

        stop_action = QAction("⏹ Stop", self._parent)
        stop_action.triggered.connect(self._tray_stop)
        menu.addAction(stop_action)

        menu.addSeparator()

        next_action = QAction("⏭ Next", self._parent)
        next_action.triggered.connect(self._tray_next)
        menu.addAction(next_action)

        prev_action = QAction("⏮ Previous", self._parent)
        prev_action.triggered.connect(self._tray_prev)
        menu.addAction(prev_action)

        menu.addSeparator()

        # Volume slider (simplified: just actions)
        vol_high = QAction("🔊 High Volume", self._parent)
        vol_high.triggered.connect(lambda: self._tray_set_volume(75))
        menu.addAction(vol_high)

        vol_low = QAction("🔉 Low Volume", self._parent)
        vol_low.triggered.connect(lambda: self._tray_set_volume(25))
        menu.addAction(vol_low)

        vol_mute = QAction("🔇 Mute", self._parent)
        vol_mute.triggered.connect(lambda: self._tray_set_volume(0))
        menu.addAction(vol_mute)

        menu.addSeparator()

        # Show main window
        show_action = QAction("📺 Show Player", self._parent)
        show_action.triggered.connect(self._tray_show_window)
        menu.addAction(show_action)

        # Quit
        quit_action = QAction("❌ Quit", self._parent)
        quit_action.triggered.connect(self._tray_quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.setToolTip("YouTube Streamer - Click to show player")
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    @Slot()
    def _tray_show_window(self):
        self._parent.show()
        self._parent.raise_()
        self._parent.activateWindow()

    @Slot()
    def _tray_play_pause(self):
        self.play_pause()

    @Slot()
    def _tray_pause(self):
        self.pause()

    @Slot()
    def _tray_stop(self):
        self.stop()

    @Slot()
    def _tray_next(self):
        self.next_track()

    @Slot()
    def _tray_prev(self):
        self.prev_track()

    @Slot()
    def _tray_set_volume(self, vol: int):
        self.set_volume(vol)

    @Slot()
    def _tray_quit(self):
        self._tray.hide()
        self._parent.close()

    @Slot()
    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_visibility()
