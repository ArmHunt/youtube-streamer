"""Data models for YouTube Streamer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class VideoInfo:
    """Parsed video metadata from yt-dlp or YouTubeI."""
    video_id: str
    title: str
    author: str
    duration: int  # seconds
    thumbnail_url: Optional[str] = None
    view_count: Optional[int] = None
    upload_date: Optional[str] = None
    description: Optional[str] = None

    @property
    def thumbnail_path(self) -> str:
        return self.thumbnail_url or ""


@dataclass
class StreamInfo:
    """A single available stream (audio or video)."""
    url: str
    format_description: str
    is_audio_only: bool
    bitrate: Optional[int] = None
    resolution: Optional[str] = None
    filesize: Optional[int] = None


@dataclass
class PlaybackQueue:
    """A playlist-like queue of videos with playback state."""
    videos: List[VideoInfo] = field(default_factory=list)
    current_index: int = 0
    autoplay: bool = True

    @property
    def current(self) -> Optional[VideoInfo]:
        if 0 <= self.current_index < len(self.videos):
            return self.videos[self.current_index]
        return None

    def next_video(self) -> Optional[VideoInfo]:
        if self.autoplay and self.current_index + 1 < len(self.videos):
            self.current_index += 1
            return self.current
        return None

    def prev_video(self) -> Optional[VideoInfo]:
        if self.current_index > 0:
            self.current_index -= 1
            return self.current
        return None
