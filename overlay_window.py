import ctypes
import json
import time
import threading
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizeGrip, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen

import keyboard as kb

from config import Config, save_config
from spotify_client import SpotifyClient
from lyrics_client import current_line_index
from lyrics_display import LyricsDisplay
from workers import SpotifyPoller, YTMusicPoller, LyricsFetcher
from settings_dialog import SettingsDialog

_CACHE_FILE = Path.home() / ".lyricoverlay" / "lyrics_cache.json"
_CACHE_MAX = 200


def _load_cache() -> dict:
    if _CACHE_FILE.exists():
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return {k: [(float(ts), text) for ts, text in v] for k, v in raw.items()}
        except Exception:
            pass
    return {}


def _save_cache(cache: dict) -> None:
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception as exc:
        print(f"[Cache] {exc}")


GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000


def _hex_alpha(hex_color: str, opacity_pct: int) -> str:
    c = QColor(hex_color)
    c.setAlpha(round(opacity_pct * 255 / 100))
    return c.name(QColor.NameFormat.HexArgb)


class OverlayWindow(QMainWindow):
    _ct_changed = pyqtSignal(bool)

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self._clickthrough = False
        self._hwnd: int = 0

        self._lyrics: list = []
        self._track_id: str | None = None
        self._fetcher: LyricsFetcher | None = None
        self._lyrics_cache: dict = _load_cache()

        self._progress_ms: float = 0.0
        self._progress_at: float = 0.0
        self._playing: bool = False
        self._last_raw_ms: float = -1.0

        self.spotify = SpotifyClient(
            config.spotify_client_id,
            config.spotify_client_secret,
        )

        self._build_ui()
        self._ct_changed.connect(self._apply_ct_ui)
        self._apply_config()
        self._register_hotkeys()
        self._start_poller()

        self._sync_timer = QTimer(self)
        self._sync_timer.timeout.connect(self._sync_lyrics)
        self._sync_timer.start(250)

    def _build_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        root = QWidget()
        root.setStyleSheet("background: transparent;")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 8, 12, 6)
        layout.setSpacing(4)

        bar = QHBoxLayout()
        bar.setSpacing(6)

        self.info_label = QLabel("No song playing")
        self.info_label.setObjectName("infoLabel")
        bar.addWidget(self.info_label, 1)

        self.ct_badge = QLabel("PASSTHROUGH")
        self.ct_badge.setObjectName("ctBadge")
        self.ct_badge.hide()
        bar.addWidget(self.ct_badge)

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setFixedSize(26, 26)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self._open_settings)
        bar.addWidget(self.settings_btn)

        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("closeBtn")
        self._close_btn.setFixedSize(26, 26)
        self._close_btn.setToolTip("Close")
        self._close_btn.clicked.connect(self._quit)
        bar.addWidget(self._close_btn)

        layout.addLayout(bar)

        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.Shape.HLine)
        self._sep.setObjectName("separator")
        layout.addWidget(self._sep)

        self.lyrics_display = LyricsDisplay(self.config)
        layout.addWidget(self.lyrics_display, 1)

        grip_row = QHBoxLayout()
        grip_row.addStretch()
        self._grip = QSizeGrip(self)
        self._grip.setFixedSize(14, 14)
        grip_row.addWidget(self._grip)
        layout.addLayout(grip_row)

    def _apply_config(self):
        c = self.config
        self.resize(c.window_width, c.window_height)
        self.move(c.window_x, c.window_y)
        # setWindowFlag recreates the native HWND even when the value is identical,
        # which crashes if called while a child dialog is still being destroyed.
        is_aot = bool(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)
        if is_aot != c.always_on_top:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, c.always_on_top)
            self._hwnd = 0
            self.show()
        self._update_stylesheet()

    def _update_stylesheet(self):
        c = self.config
        txt = _hex_alpha(c.text_color, c.text_opacity)
        self.setStyleSheet(f"""
            QWidget {{
                background: transparent;
            }}
            #infoLabel {{
                color: {txt};
                font-size: 11px;
            }}
            #ctBadge {{
                color: #f87171;
                font-size: 9px;
                font-weight: bold;
                padding: 1px 5px;
                border: 1px solid #f87171;
                border-radius: 3px;
            }}
            #settingsBtn {{
                color: {txt};
                background: transparent;
                border: none;
                font-size: 15px;
                padding: 0;
            }}
            #settingsBtn:hover {{ color: #f3f4f6; }}
            #closeBtn {{
                color: {txt};
                background: transparent;
                border: none;
                font-size: 13px;
                padding: 0;
            }}
            #closeBtn:hover {{ color: #f87171; }}
            #separator {{ color: rgba(255,255,255,20); }}
        """)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._clickthrough:
            painter.end()
            return

        bg = QColor(self.config.bg_color)
        bg.setAlpha(round(self.config.window_opacity * 255 / 100))
        painter.setBrush(bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)

        border = QColor(255, 255, 255, 20)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(border, 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._hwnd:
            self._hwnd = int(self.winId())

    def _quit(self):
        self.config.window_width = self.width()
        self.config.window_height = self.height()
        self.config.window_x = self.x()
        self.config.window_y = self.y()
        save_config(self.config)
        self._stop_poller()
        try:
            kb.unhook_all()
        except Exception:
            pass
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def closeEvent(self, event):
        self._quit()
        event.accept()

    def _register_hotkeys(self):
        try:
            kb.add_hotkey(self.config.clickthrough_hotkey, self._toggle_clickthrough)
        except Exception as exc:
            print(f"[Hotkey] {exc}")

    def _unregister_hotkeys(self):
        try:
            kb.remove_hotkey(self.config.clickthrough_hotkey)
        except Exception:
            pass

    def _toggle_clickthrough(self):
        # Called from the keyboard library's background thread — only Win32 calls
        # here; Qt UI updates go through _ct_changed signal to the main thread.
        if not self._hwnd:
            return
        self._clickthrough = not self._clickthrough
        style = ctypes.windll.user32.GetWindowLongW(self._hwnd, GWL_EXSTYLE)
        if self._clickthrough:
            style |= WS_EX_TRANSPARENT | WS_EX_LAYERED
        else:
            style &= ~WS_EX_TRANSPARENT
        ctypes.windll.user32.SetWindowLongW(self._hwnd, GWL_EXSTYLE, style)
        self._ct_changed.emit(self._clickthrough)

    @pyqtSlot(bool)
    def _apply_ct_ui(self, on: bool):
        self.info_label.setVisible(not on)
        self.ct_badge.setVisible(False)
        self.settings_btn.setVisible(not on)
        self._close_btn.setVisible(not on)
        self._sep.setVisible(not on)
        self._grip.setVisible(not on)
        self.update()

    def _open_settings(self):
        dlg = SettingsDialog(self.config, self)
        accepted = dlg.exec() == QDialog.DialogCode.Accepted
        # Defer — calling setWindowFlag/setStyleSheet while the modal dialog is
        # still being destroyed causes a crash on Windows.
        if accepted:
            QTimer.singleShot(0, self._apply_settings)

    def _apply_settings(self):
        save_config(self.config)
        self._apply_config()
        self.lyrics_display.config = self.config
        self.lyrics_display.update()
        self._unregister_hotkeys()
        self._register_hotkeys()
        self._stop_poller()
        self.spotify.reinitialize(
            self.config.spotify_client_id,
            self.config.spotify_client_secret,
        )
        self._start_poller()

    def _start_poller(self):
        if self.config.source == "ytmusic":
            self._poller = YTMusicPoller()
        else:
            self._poller = SpotifyPoller(self.spotify)
        self._poller.playback_ready.connect(self._on_playback)
        self._poller.start()

    def _stop_poller(self):
        if hasattr(self, "_poller"):
            self._poller.stop()
            self._poller.wait(2000)

    def _sync_lyrics(self):
        if not self._lyrics or not self._playing:
            return
        elapsed_ms = (time.time() - self._progress_at) * 1000
        estimated_ms = self._progress_ms + elapsed_ms
        idx = current_line_index(self._lyrics, estimated_ms / 1000)
        self.lyrics_display.set_current_index(idx)

    @pyqtSlot(object)
    def _on_playback(self, data: dict | None):
        if not data:
            self._playing = False
            if self.config.source == "ytmusic":
                self.info_label.setText("Nothing playing")
                self.lyrics_display.set_status("Play something on YouTube Music…")
            elif not self.spotify.has_credentials():
                self.info_label.setText("No song playing")
                self.lyrics_display.set_status("Connect Spotify in Settings  ⚙")
            elif not self.spotify.is_authenticated():
                self.info_label.setText("Not connected")
                self.lyrics_display.set_status("Open Settings ⚙ → Spotify → Connect")
            else:
                self.info_label.setText("Nothing playing")
                self.lyrics_display.set_status("Play something on Spotify…")
            self.lyrics_display.clear()
            self._track_id = None
            self._last_raw_ms = -1.0
            return

        fetched_at = data.get("_fetched_at", time.time())
        raw_ms: float = data["progress_ms"]
        # SMTC (YT Music) can return the same frozen position for several seconds.
        # Only reset the interpolation baseline when the reported position actually moves.
        position_moved = abs(raw_ms - self._last_raw_ms) > 150
        self._last_raw_ms = raw_ms
        if position_moved or not self._playing:
            self._progress_ms = raw_ms + (time.time() - fetched_at) * 1000
            self._progress_at = time.time()
        self._playing = True

        track_id = data["track_id"]
        self.info_label.setText(f"{data['track_name']}  —  {data['artist']}")

        if track_id != self._track_id:
            self._track_id = track_id
            self._lyrics = []

            cached = self._lyrics_cache.get(track_id)
            if cached:
                self._lyrics = cached
                self.lyrics_display.set_lyrics(cached)
            else:
                self.lyrics_display.clear()
                self.lyrics_display.set_status("Loading lyrics…")
                self._fetch_lyrics(data)

    def _fetch_lyrics(self, data: dict):
        if self._fetcher and self._fetcher.isRunning():
            self._fetcher.lyrics_ready.disconnect()
            self._fetcher.quit()

        self._fetcher = LyricsFetcher(
            data["track_id"],
            data["track_name"],
            data["artist"],
            data["album"],
            data["duration_ms"],
        )
        self._fetcher.lyrics_ready.connect(self._on_lyrics)
        self._fetcher.start()

    @pyqtSlot(object, str)
    def _on_lyrics(self, lines, track_id: str):
        if track_id != self._track_id:
            return
        if lines:
            self._lyrics = lines
            self.lyrics_display.set_lyrics(lines)
            self._lyrics_cache[track_id] = lines
            if len(self._lyrics_cache) > _CACHE_MAX:
                self._lyrics_cache.pop(next(iter(self._lyrics_cache)))
            threading.Thread(
                target=_save_cache, args=(dict(self._lyrics_cache),), daemon=True
            ).start()
        else:
            self.lyrics_display.set_status("No lyrics found for this track")
            self.lyrics_display.clear()
            self.info_label.setText(self.info_label.text() + "  (no lyrics)")
