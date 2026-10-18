"""Player engine using QtMultimedia QMediaPlayer."""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import (
    QUrl,
    QObject,
    Signal,
    Slot,
    QTimer,
    Qt,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from models import VideoInfo, PlaybackQueue

logger = logging.getLogger(__name__)


class PlayerEngine(QObject):
    """Wraps QMediaPlayer for video/audio playback with queue support."""

    # Signals
    state_changed = Signal(str)  # "playing", "paused", "stopped"
    position_changed = Signal(int)  # milliseconds
    duration_changed = Signal(int)  # milliseconds
    volume_changed = Signal(int)
    error_occurred = Signal(str)
    media_info_changed = Signal(dict)  # dict of video info

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)

        # Timer for position updates
        self._pos_timer = QTimer()
        self._pos_timer.setInterval(500)
        self._pos_timer.timeout.connect(self._on_timer_tick)

        # Volume and state tracking
        self._volume = 75
        self._current_video: Optional[VideoInfo] = None
        self._queue: Optional[PlaybackQueue] = None

        # Connect player signals
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.errorOccurred.connect(self._on_player_error)

        logger.info("PlayerEngine initialized")

    # ── Public API ────────────────────────────────────────────────

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def current_video(self) -> Optional[VideoInfo]:
        return self._current_video

    @property
    def queue(self) -> Optional[PlaybackQueue]:
        return self._queue

    @queue.setter
    def queue(self, q: Optional[PlaybackQueue]):
        self._queue = q

    def play_video(self, video: VideoInfo, stream_url: str) -> bool:
        """Play a video from a stream URL."""
        self._current_video = video
        self._player.setSource(QUrl(stream_url))
        self._player.play()
        self.media_info_changed.emit(self._make_info_dict(video))
        return True

    def play_queue_video(self, index: int) -> bool:
        """Play a video from the queue at the given index."""
        if self._queue is None or index < 0 or index >= len(self._queue.videos):
            return False
        self._queue.current_index = index
        video = self._queue.current
        if video is None:
            return False
        self._current_video = video
        # Stream URL will be set by caller via play_video()
        return True

    def play(self):
        self._player.play()

    def pause(self):
        self._player.pause()

    def stop(self):
        self._player.stop()
        self._pos_timer.stop()

    def set_volume(self, vol: int):
        """Set volume 0-100."""
        self._volume = max(0, min(100, vol))
        self._audio_output.setVolume(self._volume / 100.0)
        self.volume_changed.emit(self._volume)

    def set_position(self, ms: int):
        """Seek to position in milliseconds."""
        self._player.setPosition(ms)

    def next_video(self) -> bool:
        """Advance to next video in queue."""
        if self._queue is None:
            return False
        nxt = self._queue.next_video()
        if nxt is None:
            return False
        self._current_video = nxt
        self.media_info_changed.emit(self._make_info_dict(nxt))
        return True

    def prev_video(self) -> bool:
        """Go to previous video in queue."""
        if self._queue is None:
            return False
        prev = self._queue.prev_video()
        if prev is None:
            return False
        self._current_video = prev
        self.media_info_changed.emit(self._make_info_dict(prev))
        return True

    def get_duration_ms(self) -> int:
        return self._player.duration()

    def get_position_ms(self) -> int:
        return self._player.position()

    def is_playing(self) -> bool:
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def get_state(self) -> str:
        state = self._player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            return "playing"
        elif state == QMediaPlayer.PlaybackState.PausedState:
            return "paused"
        return "stopped"

    # ── Slot handlers ─────────────────────────────────────────────

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.state_changed.emit("playing")
            self._pos_timer.start()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.state_changed.emit("paused")
            self._pos_timer.stop()
        else:
            self.state_changed.emit("stopped")
            self._pos_timer.stop()

    def _on_position_changed(self, pos: int):
        self.position_changed.emit(pos)

    def _on_duration_changed(self, dur: int):
        self.duration_changed.emit(dur)

    def _on_player_error(self, error: QMediaPlayer.Error):
        desc = str(error)
        logger.error(f"Player error: {desc}")
        self.error_occurred.emit(desc)

    def _on_timer_tick(self):
        self.position_changed.emit(self._player.position())

    def _make_info_dict(self, video: VideoInfo) -> dict:
        return {
            "video_id": video.video_id,
            "title": video.title,
            "author": video.author,
            "duration": video.duration,
            "thumbnail_url": video.thumbnail_url or "",
        }

    def close(self):
        """Cleanup resources."""
        self.stop()
        self._player.setSource(QUrl())
        logger.info("PlayerEngine closed")
