import time

from PyQt6.QtCore import QThread, pyqtSignal

from spotify_client import SpotifyClient
from lyrics_client import fetch_lyrics, LyricLine


class SpotifyPoller(QThread):
    playback_ready = pyqtSignal(object)

    def __init__(self, client: SpotifyClient):
        super().__init__()
        self.client = client
        self._active = True

    def run(self):
        while self._active:
            try:
                data = self.client.get_current_playback()
                if data:
                    data["_fetched_at"] = time.time()
                self.playback_ready.emit(data)
            except Exception as exc:
                print(f"[Poller] {exc}")
                self.playback_ready.emit(None)
            time.sleep(1.0)

    def stop(self):
        self._active = False


class LyricsFetcher(QThread):
    lyrics_ready = pyqtSignal(object, str)

    def __init__(
        self,
        track_id: str,
        track_name: str,
        artist: str,
        album: str,
        duration_ms: int,
    ):
        super().__init__()
        self.track_id = track_id
        self.track_name = track_name
        self.artist = artist
        self.album = album
        self.duration_ms = duration_ms

    def run(self):
        lines = fetch_lyrics(
            self.track_name,
            self.artist,
            self.album,
            self.duration_ms,
        )
        self.lyrics_ready.emit(lines, self.track_id)


class YTMusicPoller(QThread):
    playback_ready = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._active = True

    def run(self):
        import ytmusic_client
        while self._active:
            try:
                data = ytmusic_client.get_current_playback()
                if data:
                    data["_fetched_at"] = time.time()
                self.playback_ready.emit(data)
            except Exception as exc:
                print(f"[YTMusicPoller] {exc}")
                self.playback_ready.emit(None)
            time.sleep(1.0)

    def stop(self):
        self._active = False
