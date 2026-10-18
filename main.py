#!/usr/bin/env python3
"""YouTube Streamer - Premium Features Unlocked

A desktop application for streaming YouTube content with:
- Picture-in-Picture mode (floating window)
- Audio playback in background (screen off)
- Ad/Sponsor blocking (via yt-dlp filters)
- Full playback controls

Usage:
    python main.py [--debug]

Author: AntonioRM
"""

from __future__ import annotations

import argparse
import logging
import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_window import MainWindow
from ytdlp_layer import YouTubeDLWrapper

logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False):
    """Configure logging for the application."""
    level = logging.DEBUG if debug else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt)

    # Suppress noisy loggers
    logging.getLogger("yt_dlp").setLevel(logging.WARNING)
    logging.getLogger("PySide6").setLevel(logging.WARNING)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="YouTube Streamer - Premium Features Unlocked")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--pi", "--pip", action="store_true", help="Start in PiP mode")
    parser.add_argument("--bg", action="store_true", help="Start with audio background mode enabled")
    parser.add_argument("--volume", type=int, default=75, help="Initial volume (0-100)")
    return parser.parse_args()


def main():
    """Application entry point."""
    args = parse_args()
    setup_logging(args.debug)

    # High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Streamer")
    app.setOrganizationName("YouTubeStreamer")
    app.setStyle("Fusion")  # Consistent cross-platform style

    # Create main window
    window = MainWindow()
    window.resize(1100, 750)

    # Apply initial settings from args
    if args.volume:
        window._volume_slider.setValue(args.volume)
        window._player.set_volume(args.volume)

    if args.pip:
        window._pip_checkbox.setChecked(True)
        window._is_pip_active = True
        window._pip_window.show()

    if args.bg:
        window._audio_bg_checkbox.setChecked(True)
        window._is_audio_bg = True

    # Show window
    window.show()
    logger.info("YouTube Streamer started")

    # Run application
    exit_code = app.exec()

    # Cleanup
    window.close()
    logger.info("YouTube Streamer exited")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
