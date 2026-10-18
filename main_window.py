"""Main application window with search, playlist, and playback controls."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, List

from PySide6.QtCore import Qt, Signal, Slot, QTimer, QThread, QUrl
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QSlider,
    QTextEdit,
    QFrame,
    QSplitter,
    QGroupBox,
    QComboBox,
    QProgressBar,
    QCheckBox,
    QMessageBox,
)

from models import VideoInfo, PlaybackQueue
from player import PlayerEngine
from ytdlp_layer import YouTubeDLWrapper
from pip_window import PiPWindow
from system_tray import SystemTrayManager

logger = logging.getLogger(__name__)

# ── Search Worker (runs in background thread) ─────────────────────


class SearchWorker(QThread):
    """Background thread for yt-dlp search operations."""

    result_ready = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, ytdlp: YouTubeDLWrapper, query: str):
        super().__init__()
        self._ytdlp = ytdlp
        self._query = query

    def run(self):
        try:
            results = self._ytdlp.search(self._query)
            self.result_ready.emit(results)
        except Exception as e:
            logger.error(f"Search worker error: {e}")
            self.error_occurred.emit(str(e))


# ── Stream Worker (runs in background thread) ────────────────────


class StreamWorker(QThread):
    """Background thread for stream extraction."""

    result_ready = Signal(object)  # StreamInfo or None
    error_occurred = Signal(str)

    def __init__(self, ytdlp: YouTubeDLWrapper, video_id: str, audio_only: bool = False):
        super().__init__()
        self._ytdlp = ytdlp
        self._video_id = video_id
        self._audio_only = audio_only

    def run(self):
        try:
            stream = self._ytdlp.get_best_stream(
                self._video_id,
                audio_only=self._audio_only,
            )
            self.result_ready.emit(stream)
        except Exception as e:
            logger.error(f"Stream worker error: {e}")
            self.error_occurred.emit(str(e))


# ── Main Window ──────────────────────────────────────────────────


class MainWindow(QMainWindow):
    """Main application window with full YouTube streaming functionality."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("YouTube Streamer - Premium Features Unlocked")
        self.setMinimumSize(1000, 700)

        # Core components
        self._ytdlp = YouTubeDLWrapper()
        self._player = PlayerEngine()
        self._pip_window = PiPWindow()
        self._pip_window.set_player(self._player)
        self._tray = SystemTrayManager(self._player, self)
        self._queue = PlaybackQueue()
        self._player.queue = self._queue

        # State
        self._current_stream_url: Optional[str] = None
        self._current_video: Optional[VideoInfo] = None
        self._history: List[VideoInfo] = []
        self._is_pip_active = False
        self._is_audio_bg = False
        self._volume = 75  # Default volume

        # Timers
        self._status_timer = QTimer()
        self._status_timer.setInterval(2000)
        self._status_timer.timeout.connect(self._update_tray_status)

        # Setup UI
        self._setup_ui()

        # Connect player signals
        self._player.state_changed.connect(self._on_state_changed)
        self._player.position_changed.connect(self._on_position_changed)
        self._player.duration_changed.connect(self._on_duration_changed)
        self._player.volume_changed.connect(self._on_volume_changed)
        self._player.error_occurred.connect(self._on_player_error)
        self._player.media_info_changed.connect(self._on_media_info_changed)

        # Load settings
        self._load_settings()

        logger.info("MainWindow initialized")

    # ── UI Construction ──────────────────────────────────────────

    def _setup_ui(self):
        """Build the complete UI layout."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # ── Top: Search bar ──────────────────────────────────────────
        search_group = QGroupBox("🔍 Search YouTube")
        search_layout = QHBoxLayout(search_group)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Enter search query (e.g., 'python tutorial')")
        self._search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self._search_input)

        self._search_btn = QPushButton("Search")
        self._search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(self._search_btn)

        self._search_mode = QComboBox()
        self._search_mode.addItems(["Videos", "Channels", "Playlists"])
        search_layout.addWidget(self._search_mode)

        main_layout.addWidget(search_group)

        # ── Middle: Splitter with search results and info ────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Search results / playlist
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        results_label = QLabel("📺 Search Results / Playlist")
        results_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        left_layout.addWidget(results_label)

        self._results_list = QListWidget()
        self._results_list.itemDoubleClicked.connect(self._on_result_selected)
        left_layout.addWidget(self._results_list)

        splitter.addWidget(left_widget)

        # Right: Video info + playback controls
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Video info panel
        info_group = QGroupBox("ℹ️ Video Information")
        info_layout = QVBoxLayout(info_group)

        self._video_thumbnail = QLabel("🖼️ Thumbnail will appear here")
        self._video_thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._video_thumbnail.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                color: #aaa;
                border: 2px dashed #444;
                min-height: 200px;
            }
        """)
        info_layout.addWidget(self._video_thumbnail)

        self._video_title = QLabel("No video selected")
        self._video_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_layout.addWidget(self._video_title)

        self._video_author = QLabel("Author: -")
        info_layout.addWidget(self._video_author)

        self._video_duration = QLabel("Duration: -")
        info_layout.addWidget(self._video_duration)

        self._video_description = QTextEdit()
        self._video_description.setReadOnly(True)
        self._video_description.setMaximumHeight(100)
        info_layout.addWidget(self._video_description)

        right_layout.addWidget(info_group)

        # ── Playback controls ────────────────────────────────────────
        controls_group = QGroupBox("🎮 Playback Controls")
        controls_layout = QVBoxLayout(controls_group)

        # Progress slider
        self._progress_slider = QSlider(Qt.Orientation.Horizontal)
        self._progress_slider.setRange(0, 1000)
        self._progress_slider.valueChanged.connect(self._on_slider_changed)
        controls_layout.addWidget(self._progress_slider)

        # Time labels
        time_layout = QHBoxLayout()
        self._current_time = QLabel("0:00")
        self._total_time = QLabel("0:00")
        time_layout.addWidget(self._current_time)
        time_layout.addStretch()
        time_layout.addWidget(self._total_time)
        controls_layout.addLayout(time_layout)

        # Control buttons
        btn_layout = QHBoxLayout()

        self._prev_btn = QPushButton("⏮ Prev")
        self._prev_btn.clicked.connect(self._on_prev)
        btn_layout.addWidget(self._prev_btn)

        self._play_btn = QPushButton("▶ Play")
        self._play_btn.clicked.connect(self._on_play_pause)
        self._play_btn.setStyleSheet("font-size: 16px; padding: 8px;")
        btn_layout.addWidget(self._play_btn)

        self._stop_btn = QPushButton("⏹ Stop")
        self._stop_btn.clicked.connect(self._on_stop)
        btn_layout.addWidget(self._stop_btn)

        self._next_btn = QPushButton("Next ⏭")
        self._next_btn.clicked.connect(self._on_next)
        btn_layout.addWidget(self._next_btn)

        controls_layout.addLayout(btn_layout)

        # Volume slider
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("🔊 Volume:"))
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(75)
        self._volume_slider.valueChanged.connect(self._on_volume_slider_changed)
        vol_layout.addWidget(self._volume_slider)
        controls_layout.addLayout(vol_layout)

        right_layout.addWidget(controls_group)

        # ── Mode toggles ─────────────────────────────────────────────
        mode_group = QGroupBox("🚀 Premium Features")
        mode_layout = QVBoxLayout(mode_group)

        self._pip_checkbox = QCheckBox("📌 Picture-in-Picture Mode")
        self._pip_checkbox.stateChanged.connect(self._on_pip_toggled)
        mode_layout.addWidget(self._pip_checkbox)

        self._audio_bg_checkbox = QCheckBox("🎵 Audio Only (Background)")
        self._audio_bg_checkbox.stateChanged.connect(self._on_audio_bg_toggled)
        mode_layout.addWidget(self._audio_bg_checkbox)

        self._no_ads_checkbox = QCheckBox("🚫 Skip Sponsor/Ads (yt-dlp filter)")
        self._no_ads_checkbox.setChecked(True)
        mode_layout.addWidget(self._no_ads_checkbox)

        right_layout.addWidget(mode_group)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

        # ── Status bar ───────────────────────────────────────────────
        self.statusBar(). showMessage("Ready - Search to start")
        self.statusBar().showMessage("Connected to YouTube via yt-dlp", 3000)

    # ── Search & Results ─────────────────────────────────────────

    @Slot()
    def _on_search(self):
        query = self._search_input.text().strip()
        if not query:
            self.statusBar().showMessage("⚠️ Enter a search query", 3000)
            return

        self._search_input.setEnabled(False)
        self._search_btn.setEnabled(False)
        self._search_btn.setText("Searching...")
        self.statusBar().showMessage(f"🔍 Searching for '{query}'...")

        # Start background search
        self._search_worker = SearchWorker(self._ytdlp, query)
        self._search_worker.result_ready.connect(self._on_search_results)
        self._search_worker.error_occurred.connect(self._on_search_error)
        self._search_worker.start()

    @Slot(list)
    def _on_search_results(self, results: list):
        self._results_list.clear()
        for video in results:
            item_text = f"{video.title} - {video.author} ({self._format_duration(video.duration)})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, video)
            self._results_list.addItem(item)

        self.statusBar().showMessage(
            f"✅ Found {len(results)} results",
            3000,
        )
        self._search_input.setEnabled(True)
        self._search_btn.setEnabled(True)
        self._search_btn.setText("Search")

    @Slot(str)
    def _on_search_error(self, error: str):
        self.statusBar().showMessage(f"❌ Search error: {error}", 5000)
        self._search_input.setEnabled(True)
        self._search_btn.setEnabled(True)
        self._search_btn.setText("Search")

    @Slot(QListWidgetItem)
    def _on_result_selected(self, item: QListWidgetItem):
        """Handle video selection from search results."""
        video = item.data(Qt.ItemDataRole.UserRole)
        if video is None:
            return

        self._select_video(video)

    def _select_video(self, video: VideoInfo):
        """Select and load a video for playback."""
        self._current_video = video
        self._video_title.setText(video.title)
        self._video_author.setText(f"Author: {video.author}")
        self._video_duration.setText(f"Duration: {self._format_duration(video.duration)}")
        self._video_description.setPlainText(
            video.description or "No description available"
        )

        # Load thumbnail
        if video.thumbnail_url:
            self._load_thumbnail(video.thumbnail_url)
        else:
            self._video_thumbnail.setText("🖼️ No thumbnail available")

        self.statusBar().showMessage(f"Selected: {video.title}")
        self._tray.set_status_text(video.title, video.author)

        # Try to play immediately (will prompt for stream quality)
        self._try_play_video(video)

    def _try_play_video(self, video: VideoInfo):
        """Extract stream and start playing."""
        self.statusBar().showMessage(f"🎬 Extracting stream for '{video.title}'...")
        audio_only = self._audio_bg_checkbox.isChecked()

        self._stream_worker = StreamWorker(
            self._ytdlp,
            video.video_id,
            audio_only=audio_only,
        )
        self._stream_worker.result_ready.connect(self._on_stream_ready)
        self._stream_worker.error_occurred.connect(self._on_stream_error)
        self._stream_worker.start()

    @Slot(object)
    def _on_stream_ready(self, stream):
        if stream is None:
            self.statusBar().showMessage("❌ No stream available", 3000)
            return

        self._current_stream_url = stream.url
        self._add_to_history(self._current_video)

        if self._is_pip_active:
            self._pip_window.play_video(
                self._current_video.video_id,
                stream.url,
            )
        else:
            self._player.play_video(
                self._current_video,
                stream.url,
            )
            self._player.play()

        self.statusBar().showMessage(f"▶ Playing: {self._current_video.title}")
        self._status_timer.start()

    @Slot(str)
    def _on_stream_error(self, error: str):
        self.statusBar().showMessage(f"❌ Stream error: {error}", 5000)

    def _load_thumbnail(self, url: str):
        """Load thumbnail from URL."""
        try:
            import urllib.request
            import tempfile
            import os

            # Download thumbnail to temp file
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = tmp.name
                urllib.request.urlretrieve(url, tmp_path)

                # Load into QPixmap
                pixmap = QPixmap(tmp_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        self._video_thumbnail.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    self._video_thumbnail.setPixmap(scaled)
                else:
                    self._video_thumbnail.setText("🖼️ Failed to load thumbnail")

                # Cleanup
                os.unlink(tmp_path)
        except Exception as e:
            logger.error(f"Thumbnail load error: {e}")
            self._video_thumbnail.setText("🖼️ Thumbnail load failed")

    # ── Playback Controls ────────────────────────────────────────

    @Slot()
    def _on_play_pause(self):
        if self._player.is_playing():
            self._player.pause()
            self._play_btn.setText("▶ Play")
        else:
            if self._current_stream_url:
                self._player.play()
                self._play_btn.setText("⏸ Pause")
            else:
                self.statusBar().showMessage("⚠️ No video loaded", 2000)

    @Slot()
    def _on_stop(self):
        self._player.stop()
        self._play_btn.setText("▶ Play")
        self._progress_slider.setValue(0)
        self._current_time.setText("0:00")
        self._total_time.setText("0:00")

    @Slot()
    def _on_prev(self):
        self._player.prev_video()

    @Slot()
    def _on_next(self):
        self._player.next_video()

    @Slot(int)
    def _on_slider_changed(self, value: int):
        """Handle progress slider changes."""
        # Convert slider value to milliseconds
        duration = self._player.get_duration_ms()
        if duration > 0:
            pos_ms = int(value / 1000.0 * duration)
            self._player.set_position(pos_ms)

    @Slot(int)
    def _on_volume_slider_changed(self, value: int):
        self._player.set_volume(value)

    @Slot(str)
    def _on_state_changed(self, state: str):
        if state == "playing":
            self._play_btn.setText("⏸ Pause")
        elif state == "paused":
            self._play_btn.setText("▶ Play")
        else:
            self._play_btn.setText("▶ Play")

    @Slot(int)
    def _on_position_changed(self, pos_ms: int):
        duration = self._player.get_duration_ms()
        if duration > 0:
            slider_val = int(pos_ms / duration * 1000)
            self._progress_slider.blockSignals(True)
            self._progress_slider.setValue(slider_val)
            self._progress_slider.blockSignals(False)
            self._current_time.setText(self._format_time(pos_ms))

    @Slot(int)
    def _on_duration_changed(self, dur_ms: int):
        self._total_time.setText(self._format_time(dur_ms))
        self._progress_slider.setRange(0, 1000)

    @Slot(int)
    def _on_volume_changed(self, vol: int):
        self._volume_slider.blockSignals(True)
        self._volume_slider.setValue(vol)
        self._volume_slider.blockSignals(False)

    @Slot(str)
    def _on_player_error(self, error: str):
        """Handle player errors."""
        self.statusBar().showMessage(f"❌ Player error: {error}", 5000)
        logger.error(f"Player error: {error}")

    @Slot(int)
    def _on_volume_changed(self, vol: int):
        """Update volume slider when player volume changes."""
        self._volume_slider.blockSignals(True)
        self._volume_slider.setValue(vol)
        self._volume_slider.blockSignals(False)

    @Slot(dict)
    def _on_media_info_changed(self, info: dict):
        """Update UI with new media information."""
        title = info.get("title", "Unknown")
        author = info.get("author", "Unknown")
        self._tray.set_status_text(title, author)

    # ── Premium Features ─────────────────────────────────────────

    @Slot(int)
    def _on_pip_toggled(self, state: int):
        self._is_pip_active = (state == 2)  # Checked
        if self._is_pip_active and self._current_stream_url:
            self._pip_window.play_video(
                self._current_video.video_id,
                self._current_stream_url,
            )
        self.statusBar().showMessage(
            "📌 PiP mode: " + ("ON" if self._is_pip_active else "OFF"),
            2000,
        )

    @Slot(int)
    def _on_audio_bg_toggled(self, state: int):
        self._is_audio_bg = (state == 2)  # Checked
        self.statusBar().showMessage(
            "🎵 Audio BG: " + ("ON" if self._is_audio_bg else "OFF"),
            2000,
        )

    # ── History & Queue ──────────────────────────────────────────

    def _add_to_history(self, video: VideoInfo):
        """Add video to playback history."""
        self._history.append(video)
        if len(self._history) > 100:
            self._history = self._history[-50:]

    def _update_tray_status(self):
        """Periodically update tray tooltip."""
        if self._current_video:
            self._tray.set_status_text(
                self._current_video.title,
                self._format_duration(self._current_video.duration),
            )

    # ── Settings ─────────────────────────────────────────────────

    def _load_settings(self):
        """Load application settings from config file."""
        config_path = Path.home() / ".config" / "youtube-streamer" / "settings.json"
        if config_path.exists():
            try:
                import json
                with open(config_path) as f:
                    settings = json.load(f)
                    vol = settings.get("volume", 75)
                    self._volume_slider.setValue(vol)
                    self._player.set_volume(vol)
                logger.info("Settings loaded")
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")

    def save_settings(self):
        """Save application settings."""
        try:
            config_dir = Path.home() / ".config" / "youtube-streamer"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "settings.json"

            import json
            settings = {
                "volume": self._volume,
            }
            with open(config_path, "w") as f:
                json.dump(settings, f, indent=2)
            logger.info("Settings saved")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    # ── Window Events ────────────────────────────────────────────

    def closeEvent(self, event):
        """Handle window close."""
        self.save_settings()
        self._player.close()
        self._pip_window.close()
        self._tray._tray.hide()
        self._ytdlp.close()
        event.accept()

    # ── Utilities ────────────────────────────────────────────────

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format seconds to HH:MM:SS or MM:SS."""
        if seconds <= 0:
            return "0:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    @staticmethod
    def _format_time(ms: int) -> str:
        """Format milliseconds to MM:SS."""
        if ms <= 0:
            return "0:00"
        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
