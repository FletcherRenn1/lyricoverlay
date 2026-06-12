import webbrowser
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional, Callable

import spotipy
from spotipy.oauth2 import SpotifyOAuth

CACHE_PATH = Path.home() / ".lyricoverlay" / ".spotify_cache"
SCOPE = "user-read-currently-playing user-read-playback-state"
REDIRECT_URI = "http://127.0.0.1:8888/callback"


class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str):
        self.sp: Optional[spotipy.Spotify] = None
        self._auth: Optional[SpotifyOAuth] = None
        self.client_id = client_id
        self.client_secret = client_secret
        if client_id and client_secret:
            self._init(client_id, client_secret)

    def _init(self, client_id: str, client_secret: str):
        self._auth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            cache_path=str(CACHE_PATH),
            open_browser=False,
        )
        token = self._auth.get_cached_token()
        if token:
            self.sp = spotipy.Spotify(auth_manager=self._auth)

    def reinitialize(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.sp = None
        self._auth = None
        if client_id and client_secret:
            self._init(client_id, client_secret)

    def has_credentials(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def is_authenticated(self) -> bool:
        if not self._auth:
            return False
        try:
            token = self._auth.get_cached_token()
            return token is not None
        except Exception:
            return False

    def start_oauth(
        self,
        on_success: Callable[[], None],
        on_error: Callable[[str], None],
    ):
        t = threading.Thread(
            target=self._oauth_thread, args=(on_success, on_error), daemon=True
        )
        t.start()

    def _oauth_thread(self, on_success, on_error):
        try:
            auth_url = self._auth.get_authorize_url()
            webbrowser.open(auth_url)
            code = self._capture_callback()
            if not code:
                on_error("Authentication timed out. Please try again.")
                return
            self._auth.get_access_token(code, as_dict=False, check_cache=False)
            self.sp = spotipy.Spotify(auth_manager=self._auth)
            on_success()
        except Exception as exc:
            on_error(str(exc))

    def _capture_callback(self, timeout: int = 120) -> Optional[str]:
        received: list[Optional[str]] = [None]

        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                params = urllib.parse.parse_qs(
                    urllib.parse.urlparse(self.path).query
                )
                if "code" in params:
                    received[0] = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    b"<html><body style='font-family:sans-serif;"
                    b"text-align:center;margin-top:80px'>"
                    b"<h1 style='color:#1DB954'>Connected to Spotify!</h1>"
                    b"<p>You can close this tab and return to LyricOverlay.</p>"
                    b"</body></html>"
                )

            def log_message(self, *_):
                pass

        try:
            server = HTTPServer(("127.0.0.1", 8888), _Handler)
            server.timeout = timeout
            server.handle_request()
        except Exception:
            pass
        return received[0]

    def get_current_playback(self) -> Optional[dict]:
        if not self.sp:
            return None
        try:
            pb = self.sp.current_playback()
            if not pb or not pb.get("is_playing"):
                return None
            if pb.get("currently_playing_type") != "track":
                return None
            track = pb.get("item")
            if not track:
                return None
            return {
                "track_id": track["id"],
                "track_name": track["name"],
                "artist": ", ".join(a["name"] for a in track["artists"]),
                "album": track["album"]["name"],
                "progress_ms": pb["progress_ms"],
                "duration_ms": track["duration_ms"],
            }
        except Exception as exc:
            print(f"[Spotify] {exc}")
            return None
