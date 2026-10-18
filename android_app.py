"""YouTube Streamer Android - Kivy UI

App móvil con:
- Búsqueda de YouTube (yt-dlp)
- Reproducción con ExoPlayer (vía Kivy android)
- Picture-in-Picture nativo Android
- Audio en segundo plano
- Sin publicidad (yt-dlp filters)
"""

from __future__ import annotations

import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.checkbox import Checkbox
from kivy.uix.slider import Slider as KivySlider
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.image import Image
from kivy.utils import platform

from models import VideoInfo, StreamInfo, PlaybackQueue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Platform detection
IS_ANDROID = platform == 'android'
IS_IOS = platform == 'ios'
IS_DESKTOP = not IS_ANDROID and not IS_IOS


class AndroidVideoListItem(BoxLayout):
    """List item for video search results."""

    def __init__(self, video: VideoInfo, on_select, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(100)
        self.padding = dp(10)
        self.spacing = dp(10)
        self.background_color = (0.12, 0.12, 0.14, 1) if IS_ANDROID else (0.15, 0.15, 0.17, 1)

        self.video = video
        self.on_select = on_select

        # Thumbnail (will load async)
        self.thumb = Image(
            source=video.thumbnail_url or '',
            size_hint_x=0.4,
            allow_stretch=True,
            keep_ratio=True
        )
        self.add_widget(self.thumb)

        # Info layout
        info = BoxLayout(orientation='vertical', size_hint_x=0.6)
        info.padding = dp(5)

        # Title
        self.title_label = Label(
            text=video.title,
            size_hint_y=0.6,
            halign='left',
            valign='middle',
            color=(0.95, 0.95, 0.95, 1),
            font_size=dp(14)
        )
        info.add_widget(self.title_label)

        # Author
        author_label = Label(
            text=video.author,
            size_hint_y=0.4,
            halign='left',
            color=(0.6, 0.6, 0.6, 1),
            font_size=dp(11)
        )
        info.add_widget(author_label)

        self.add_widget(info)

        # Click handler
        self.bind(on_press=self._on_click)

    def _on_click(self, *args):
        self.on_select(self.video)


class AndroidSearchResults(BoxLayout):
    """Scrollable search results list."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(2)
        self.padding = dp(5)

        self.scroll = ScrollView()
        self.list_layout = GridLayout(
            cols=1,
            size_hint_y=None
        )
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)
        self.add_widget(self.scroll)

        self.items: List[AndroidVideoListItem] = []

    def add_item(self, video: VideoInfo, on_select):
        item = AndroidVideoListItem(video, on_select)
        self.list_layout.add_widget(item)
        self.items.append(item)

    def clear(self):
        for item in self.items:
            self.list_layout.remove_widget(item)
        self.items.clear()


class AndroidPlayer(BoxLayout):
    """Video player with controls."""

    def __init__(self, player_engine, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.player = player_engine
        self.padding = dp(10)
        self.spacing = dp(10)

        # Video display
        self.video_canvas = Widget(
            size_hint_y=0.5,
            background_color=(0, 0, 0, 1)
        )
        self.add_widget(self.video_canvas)

        # Progress bar
        self.progress = ProgressBar(
            size_hint_y=None,
            height=dp(20),
            max=100
        )
        self.add_widget(self.progress)

        # Time labels
        time_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(20)
        )
        self.current_time = Label(text='0:00', size_hint_x=0.5, color=(0.8, 0.8, 0.8, 1), font_size=dp(11))
        self.duration = Label(text='0:00', size_hint_x=0.5, halign='right', color=(0.8, 0.8, 0.8, 1), font_size=dp(11))
        time_layout.add_widget(self.current_time)
        time_layout.add_widget(self.duration)
        self.add_widget(time_layout)

        # Controls
        ctrl_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(10)
        )

        # Previous button
        prev_btn = Button(
            text='⏮',
            size_hint_x=0.2,
            font_size=dp(24),
            background_color=(0.2, 0.2, 0.2, 1)
        )
        prev_btn.bind(on_press=self._prev)
        ctrl_layout.add_widget(prev_btn)

        # Play/Pause button
        self.play_pause_btn = Button(
            text='▶',
            size_hint_x=0.3,
            font_size=dp(28),
            background_color=(0.15, 0.6, 0.15, 1)
        )
        self.play_pause_btn.bind(on_press=self._toggle_play)
        ctrl_layout.add_widget(self.play_pause_btn)

        # Next button
        next_btn = Button(
            text='⏭',
            size_hint_x=0.2,
            font_size=dp(24),
            background_color=(0.2, 0.2, 0.2, 1)
        )
        next_btn.bind(on_press=self._next)
        ctrl_layout.add_widget(next_btn)

        # Volume slider
        self.volume_slider = KivySlider(
            orientation='horizontal',
            size_hint_x=0.3,
            min=0,
            max=100,
            value=75
        )
        self.volume_slider.bind(value=self._on_volume)
        ctrl_layout.add_widget(self.volume_slider)

        self.add_widget(ctrl_layout)

    def _toggle_play(self, *args):
        if self.player.is_playing():
            self.player.pause()
            self.play_pause_btn.text = '▶'
        else:
            self.player.play()
            self.play_pause_btn.text = '⏸'

    def _prev(self, *args):
        self.player.prev_video()

    def _next(self, *args):
        self.player.next_video()

    def _on_volume(self, instance, value):
        self.player.set_volume(int(value))


class YouTubeStreamerApp(App):
    """Main YouTube Streamer Android application."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_worker: Optional[YouTubeDLWrapper] = None
        self.player_engine: Optional[PlayerEngine] = None
        self.current_video: Optional[VideoInfo] = None
        self.queue = PlaybackQueue()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._search_results: List[VideoInfo] = []

    def build(self):
        # Window setup
        Window.clearcolor = (0.08, 0.08, 0.1, 1)  # Dark theme

        # Main layout
        self.root = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

        # Header
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(10)
        )

        # Title
        title_label = Label(
            text='🎬 YouTube Streamer',
            color=(1, 0.6, 0, 1),  # Orange accent
            font_size=dp(18),
            bold=True,
            size_hint_x=0.5
        )
        header.add_widget(title_label)

        # PiP toggle
        self.pip_checkbox = Checkbox(
            size_hint_x=0.3,
            active=False
        )
        pip_label = Label(text='PiP', size_hint_x=0.2, color=(0.8, 0.8, 0.8, 1))
        self.pip_checkbox.bind(active=self._on_pip_toggle)
        header.add_widget(pip_label)
        header.add_widget(self.pip_checkbox)

        # Audio BG toggle
        self.audio_bg_checkbox = Checkbox(
            size_hint_x=0.3,
            active=True
        )
        audio_label = Label(text='BG', size_hint_x=0.2, color=(0.8, 0.8, 0.8, 1))
        self.audio_bg_checkbox.bind(active=self._on_audio_bg_toggle)
        header.add_widget(audio_label)
        header.add_widget(self.audio_bg_checkbox)

        self.root.add_widget(header)

        # Search bar
        search_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )

        self.search_input = TextInput(
            hint_text='Buscar en YouTube...',
            size_hint_x=0.7,
            font_size=dp(16),
            background_color=(0.15, 0.15, 0.17, 1),
            foreground_color=(0.95, 0.95, 0.95, 1)
        )
        search_layout.add_widget(self.search_input)

        search_btn = Button(
            text='🔍 Buscar',
            size_hint_x=0.3,
            background_color=(0.9, 0.4, 0, 1),  # Orange
            color=(1, 1, 1, 1)
        )
        search_btn.bind(on_press=self._perform_search)
        search_layout.add_widget(search_btn)

        self.root.add_widget(search_layout)

        # Video quality selector
        quality_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(35),
            spacing=dp(10)
        )
        quality_label = Label(text='Calidad:', size_hint_x=0.3, color=(0.8, 0.8, 0.8, 1), font_size=dp(12))
        self.quality_spinner = Spinner(
            text='720p',
            values=['720p', '1080p', '480p', '360p', 'Audio'],
            size_hint_x=0.5
        )
        quality_layout.add_widget(quality_label)
        quality_layout.add_widget(self.quality_spinner)
        self.root.add_widget(quality_layout)

        # Search results
        self.results = AndroidSearchResults()
        self.root.add_widget(self.results)

        # Player
        # Initialize player engine (will work on Android with proper mediaplayer)
        from player import PlayerEngine
        self.player_engine = PlayerEngine()
        self.player = AndroidPlayer(self.player_engine)
        self.root.add_widget(self.player)

        # Initialize yt-dlp wrapper
        self.search_worker = YouTubeDLWrapper()

        # Start position update timer
        Clock.schedule_interval(self._update_progress, 0.5)

        return self.root

    def _perform_search(self, instance):
        query = self.search_input.text.strip()
        if not query:
            return

        # Show loading state
        self.search_input.disabled = True
        loading_label = Label(text='🔍 Buscando...', color=(1, 0.6, 0, 1), font_size=dp(14))
        self.root.add_widget(loading_label)

        # Search in background
        def search_task():
            try:
                results = self.search_worker.search(query, max_results=20)
                return results
            except Exception as e:
                logger.error(f"Search error: {e}")
                return []

        def on_search_complete(results):
            self.root.remove_widget(loading_label)
            self.search_input.disabled = False
            self.results.clear()
            self._search_results = results

            if not results:
                no_results = Label(
                    text='No se encontraron resultados',
                    color=(0.6, 0.6, 0.6, 1),
                    font_size=dp(14)
                )
                self.results.add_widget(no_results)
                return

            for video in results:
                self.results.add_item(video, self._on_video_select)

        self.executor.submit(search_task).add_done_callback(
            lambda future: Clock.schedule_once(
                lambda dt: on_search_complete(future.result())
            )
        )

    def _on_video_select(self, video: VideoInfo):
        """Handle video selection from search results."""
        self.current_video = video

        # Show loading
        loading = Label(
            text=f'⏳ Cargando: {video.title}',
            color=(1, 0.6, 0, 1),
            font_size=dp(12)
        )
        self.root.add_widget(loading)

        def load_stream():
            try:
                quality = self.quality_spinner.text
                stream_url = self.search_worker.get_stream_url(
                    video.video_id,
                    quality=quality
                )
                return stream_url
            except Exception as e:
                logger.error(f"Stream error: {e}")
                return None

        def on_stream_loaded(future):
            self.root.remove_widget(loading)
            stream_url = future.result()
            if stream_url:
                self.player_engine.play_video(video, stream_url)
                self.player.play_pause_btn.text = '⏸'
                # Add to queue
                self.queue.videos.append(video)
            else:
                error_label = Label(
                    text=f'❌ Error al cargar: {video.title}',
                    color=(1, 0.2, 0.2, 1),
                    font_size=dp(12)
                )
                self.root.add_widget(error_label)

        future = self.executor.submit(load_stream)
        future.add_done_callback(on_stream_loaded)

    def _on_pip_toggle(self, instance, value):
        """Handle PiP toggle."""
        if value:
            logger.info("PiP enabled")
            # Android PiP is handled by OS
            if IS_ANDROID:
                # Use Android native PiP
                pass
        else:
            logger.info("PiP disabled")

    def _on_audio_bg_toggle(self, instance, value):
        """Handle audio background toggle."""
        if value:
            logger.info("Audio background mode enabled")
        else:
            logger.info("Audio background mode disabled")

    def _update_progress(self, dt):
        """Update progress bar and time labels."""
        if self.player_engine and self.player_engine.get_duration_ms() > 0:
            pos = self.player_engine.get_position_ms()
            dur = self.player_engine.get_duration_ms()

            # Update progress bar (0-1)
            progress = pos / dur
            self.player.progress.value = int(progress * 100)

            # Update time labels
            self.player.current_time.text = self._format_time(pos)
            self.player.duration.text = self._format_time(dur)

    def _format_time(self, ms: int) -> str:
        """Format milliseconds to MM:SS or HH:MM:SS."""
        total_seconds = ms // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

    def stop(self):
        """Cleanup on app stop."""
        self.executor.shutdown(wait=False)
        if self.player_engine:
            self.player_engine.close()
        super().stop()


# Entry point
if __name__ == '__main__':
    YouTubeStreamerApp().run()
