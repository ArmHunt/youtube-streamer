"""yt-dlp layer for stream extraction and searching."""

from __future__ import annotations

import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any

import yt_dlp

from models import VideoInfo, StreamInfo

logger = logging.getLogger(__name__)

# Global ytdlp instance with default opts
YTDLP_DEFAULT_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "noplaylist": False,
}


class YouTubeDLWrapper:
    """Thin wrapper around yt-dlp for searching, metadata, and stream extraction."""

    def __init__(self, opts: Optional[Dict[str, Any]] = None):
        self._opts = {**YTDLP_DEFAULT_OPTS, **(opts or {})}
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ytdlp")

    def search(self, query: str, max_results: int = 10) -> List[VideoInfo]:
        """Search YouTube and return VideoInfo objects."""
        results: List[VideoInfo] = []
        search_opts = {
            **self._opts,
            "extract_flat": False,
        }

        def _fetch():
            videos: List[VideoInfo] = []
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                # First pass: get IDs only for speed
                ids_opts = {
                    **search_opts,
                    "extract_flat": "in_playlist",
                    "playlistend": max_results,
                    "dump_single_json": False,
                }
                info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                entries = info.get("entries")
                if entries is None:
                    return videos
                for entry in entries:
                    if entry is None:
                        continue
                    v = VideoInfo(
                        video_id=str(entry.get("id", "")),
                        title=str(entry.get("title", "Unknown")),
                        author=str(entry.get("uploader", "Unknown")),
                        duration=entry.get("duration", 0) or 0,
                        thumbnail_url=entry.get("thumbnail"),
                        view_count=entry.get("view_count"),
                        upload_date=entry.get("upload_date"),
                        description=str(entry.get("description", ""))[:200],
                    )
                    if v.video_id:
                        videos.append(v)
            return videos

        try:
            future = self._executor.submit(_fetch)
            results = future.result(timeout=30)
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")

        return results

    def get_video_info(self, video_id: str) -> Optional[VideoInfo]:
        """Get detailed metadata for a single video."""
        opts = {**self._opts, "extract_flat": False}

        def _fetch():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                if not info:
                    return None
                return VideoInfo(
                    video_id=str(info.get("id", video_id)),
                    title=str(info.get("title", "Unknown")),
                    author=str(info.get("uploader", "Unknown")),
                    duration=info.get("duration", 0) or 0,
                    thumbnail_url=info.get("thumbnail"),
                    view_count=info.get("view_count"),
                    upload_date=info.get("upload_date"),
                    description=str(info.get("description", ""))[:500],
                )

        try:
            future = self._executor.submit(_fetch)
            return future.result(timeout=30)
        except Exception as e:
            logger.error(f"get_video_info failed for {video_id}: {e}")
            return None

    def get_streams(self, video_id: str, prefer_best: bool = True) -> List[StreamInfo]:
        """Get all available streams for a video (audio-only, video-only, combined)."""
        streams: List[StreamInfo] = []
        opts = {**self._opts, "extract_flat": False}

        def _fetch():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                formats = info.get("formats", [])
                seen_urls: set = set()

                # Group formats by format_id
                groups: Dict[str, list] = {}
                for fmt in formats:
                    fmt_id = str(fmt.get("format_id", ""))
                    if not fmt_id:
                        continue
                    groups.setdefault(fmt_id, []).append(fmt)

                # Classify each group
                for fmt_id, fmts in groups.items():
                    best = max(fmts, key=lambda f: int(f.get("filesize", 0) or f.get("filesize_approx", 0) or 0))
                    url = best.get("url", "")
                    if not url or url in seen_urls:
                        continue

                    is_audio = best.get("vcodec") == "none" and best.get("acodec") != "none"
                    is_video = best.get("acodec") == "none" and best.get("vcodec") != "none"

                    stream = StreamInfo(
                        url=url,
                        format_description=best.get("format_note", best.get("format", "")),
                        is_audio_only=is_audio,
                        bitrate=best.get("abr") or best.get("br"),
                        resolution=_format_resolution(best),
                        filesize=best.get("filesize") or best.get("filesize_approx"),
                    )
                    streams.append(stream)
                    seen_urls.add(url)

            return streams

        try:
            future = self._executor.submit(_fetch)
            result = future.result(timeout=30)
            # Sort: prefer video, then by resolution
            result.sort(key=lambda s: (s.is_audio_only, -int(s.bitrate or 0)), reverse=prefer_best)
            return result
        except Exception as e:
            logger.error(f"get_streams failed for {video_id}: {e}")
            return []

    def get_best_stream(self, video_id: str, audio_only: bool = False) -> Optional[StreamInfo]:
        """Get the best available stream (or audio-only if requested)."""
        streams = self.get_streams(video_id)
        if audio_only:
            audio_streams = [s for s in streams if s.is_audio_only]
            return audio_streams[0] if audio_streams else (streams[0] if streams else None)
        # Return best video stream (not audio-only)
        video_streams = [s for s in streams if not s.is_audio_only]
        return video_streams[0] if video_streams else (streams[0] if streams else None)

    def download_thumbnail(self, video_id: str, output_path: Optional[str] = None) -> Optional[str]:
        """Download a video thumbnail to local file. Returns local path or None."""
        opts = {**self._opts, "extract_flat": False}

        def _fetch():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                thumb_url = info.get("thumbnail")
                if not thumb_url:
                    return None
                # Build local path
                if output_path is None:
                    import os
                    output_path = os.path.join("/tmp", f"yt_thumb_{video_id}.jpg")
                # Try to download
                try:
                    import urllib.request
                    urllib.request.urlretrieve(thumb_url, output_path)
                except Exception as e:
                    logger.error(f"Failed to download thumbnail: {e}")
                    return None
                return output_path

        try:
            future = self._executor.submit(_fetch)
            return future.result(timeout=15)
        except Exception as e:
            logger.error(f"thumbnail download failed: {e}")
            return None

    def close(self):
        self._executor.shutdown(wait=False)


def _format_resolution(fmt: Dict) -> Optional[str]:
    """Extract resolution string from a yt-dlp format dict."""
    width = fmt.get("width") or fmt.get("resolution")
    height = fmt.get("height")
    if height and width:
        return f"{width}x{height}"
    return None
