"""YouTube Streamer Android - Entry Point

App móvil con:
- Búsqueda de YouTube (yt-dlp)
- Reproducción con Kivy Video
- Picture-in-Picture nativo Android
- Audio en segundo plano
- Sin publicidad (yt-dlp filters)
"""

from __future__ import annotations

import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.clock import Clock

sys.path.insert(0, os.path.dirname(__file__))

from models import VideoInfo, PlaybackQueue
from ytdlp_layer import YouTubeDLWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoListItem(BoxLayout):
    """List item for video search results."""

    def __init__(self, video: VideoInfo, on_select, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(100)
        self.padding = dp(10)
        self.spacing = dp(10)
        self.background_color = (0.12, 0.12, 0.14, 1)

        self.video = video
        self.on_select = on_select

        # Thumbnail placeholder
        thumb = Widget(
            size_hint_x=0.4,
            background_color=(0.2, 0.2, 0.2, 1)
        )
        self.add_widget(thumb)

        # Info
        info = BoxLayout(
            orientation='vertical',
            size_hint_x=0.6,
            padding=dp(5)
        )
        self.title_label = Label(
            text=video.title,
            size_hint_y=0.6,
            halign='left',
            valign='middle',
            color=(0.95, 0.95, 0.95, 1),
            font_size=dp(14)
        )
        info.add_widget(self.title_label)
        author_label = Label(
            text=video.author,
            size_hint_y=0.4,
            halign='left',
            color=(0.6, 0.6, 0.6, 1),
            font_size=dp(11)
        )
        info.add_widget(author_label)
        self.add_widget(info)

        self.bind(on_press=self._on_click)

    def _on_click(self, *args):
        self.on_select(self.video)


class YouTubeStreamerApp(App):
    """Main YouTube Streamer Android application."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_worker = YouTubeDLWrapper()
        self.current_video: Optional[VideoInfo] = None
        self.queue = PlaybackQueue()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._search_results: List[VideoInfo] = []

    def build(self):
        Window.clearcolor = (0.08, 0.08, 0.1, 1)

        # Main layout
        self.root = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            padding=dp(10)
        )

        # Header
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(10)
        )

        title = Label(
            text='YouTube Streamer',
            color=(1, 0.6, 0, 1),
            font_size=dp(18),
            bold=True,
            size_hint_x=0.5
        )
        header.add_widget(title)

        self.pip_label = Label(
            text='PiP: OFF',
            size_hint_x=0.3,
            color=(0.8, 0.8, 0.8, 1),
            font_size=dp(12)
        )
        header.add_widget(self.pip_label)

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
            text='Buscar',
            size_hint_x=0.3,
            background_color=(0.9, 0.4, 0, 1),
            color=(1, 1, 1, 1)
        )
        search_btn.bind(on_press=self._perform_search)
        search_layout.add_widget(search_btn)

        self.root.add_widget(search_layout)

        # Quality selector
        quality_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(35),
            spacing=dp(10)
        )
        quality_label = Label(
            text='Calidad:',
            size_hint_x=0.3,
            color=(0.8, 0.8, 0.8, 1),
            font_size=dp(12)
        )
        self.quality_spinner = Spinner(
            text='720p',
            values=['720p', '1080p', '480p', '360p', 'Audio'],
            size_hint_x=0.5
        )
        quality_layout.add_widget(quality_label)
        quality_layout.add_widget(self.quality_spinner)
        self.root.add_widget(quality_layout)

        # Search results
        self.results_layout = GridLayout(
            cols=1,
            size_hint_y=None,
            minimum_height=dp(200)
        )
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))

        self.scroll = ScrollView()
        self.scroll.add_widget(self.results_layout)
        self.root.add_widget(self.scroll)

        # Player info
        self.player_info = Label(
            text='Selecciona un video para reproducir',
            color=(0.8, 0.8, 0.8, 1),
            font_size=dp(12),
            halign='center'
        )
        self.root.add_widget(self.player_info)

        return self.root

    def _perform_search(self, instance):
        query = self.search_input.text.strip()
        if not query:
            return

        # Clear previous results
        for widget in self.results_layout.children[:]:
            self.results_layout.remove_widget(widget)

        self.search_input.disabled = True
        loading = Label(
            text='Buscando...',
            color=(1, 0.6, 0, 1),
            font_size=dp(14)
        )
        self.results_layout.add_widget(loading)

        def search_task():
            try:
                return self.search_worker.search(query, max_results=20)
            except Exception as e:
                logger.error(f"Search error: {e}")
                return []

        def on_search_complete(results):
            self.results_layout.remove_widget(loading)
            self.search_input.disabled = False
            self._search_results = results

            if not results:
                no_results = Label(
                    text='No se encontraron resultados',
                    color=(0.6, 0.6, 0.6, 1),
                    font_size=dp(14)
                )
                self.results_layout.add_widget(no_results)
                return

            for video in results:
                item = VideoListItem(video, self._on_video_select)
                self.results_layout.add_widget(item)

        self.executor.submit(search_task).add_done_callback(
            lambda future: Clock.schedule_once(
                lambda dt: on_search_complete(future.result())
            )
        )

    def _on_video_select(self, video: VideoInfo):
        self.current_video = video

        loading = Label(
            text=f'Cargando: {video.title}',
            color=(1, 0.6, 0, 1),
            font_size=dp(12)
        )
        self.results_layout.add_widget(loading)

        def load_stream():
            try:
                quality = self.quality_spinner.text
                return self.search_worker.get_stream_url(video.video_id, quality=quality)
            except Exception as e:
                logger.error(f"Stream error: {e}")
                return None

        def on_stream_loaded(future):
            self.results_layout.remove_widget(loading)
            stream_url = future.result()
            if stream_url:
                self.player_info.text = f'Reproduciendo: {video.title}'
                self.player_info.color = (0.2, 0.8, 0.2, 1)
                self.queue.videos.append(video)
            else:
                self.player_info.text = f'Error al cargar: {video.title}'
                self.player_info.color = (1, 0.2, 0.2, 1)

        future = self.executor.submit(load_stream)
        future.add_done_callback(on_stream_loaded)


if __name__ == '__main__':
    YouTubeStreamerApp().run()
