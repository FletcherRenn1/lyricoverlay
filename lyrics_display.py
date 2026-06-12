from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QFont, QColor

from config import Config
from lyrics_client import LyricLine


class LyricsDisplay(QWidget):
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.lyrics: list[LyricLine] = []
        self.current_index: int = 0
        self._render_pos: float = 0.0
        self._target_pos: float = 0.0
        self._status: str = "Connect Spotify in Settings  ⚙"

        # Use stylesheet transparency, not WA_TranslucentBackground — on Windows
        # layered windows, WA_TranslucentBackground forces alpha=0 on child widgets
        # which makes them permanently click-through regardless of window state.
        self.setStyleSheet("background: transparent;")
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._drag_pos = None

        tick = QTimer(self)
        tick.timeout.connect(self._animate)
        tick.start(16)

    def set_lyrics(self, lyrics: list[LyricLine]):
        self.lyrics = lyrics
        self.current_index = 0
        self._render_pos = 0.0
        self._target_pos = 0.0
        self.update()

    def set_current_index(self, index: int):
        if index == self.current_index:
            return
        self.current_index = index
        self._target_pos = float(index)
        self.update()

    def set_status(self, msg: str):
        self._status = msg
        self.update()

    def clear(self):
        self.lyrics = []
        self.current_index = 0
        self._render_pos = 0.0
        self._target_pos = 0.0
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            win = self.window()
            win.move(win.pos() + event.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        event.accept()

    def _animate(self):
        diff = self._target_pos - self._render_pos
        if abs(diff) > 0.004:
            self._render_pos += diff * 0.13
            self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        if not self.lyrics:
            self._paint_idle(painter)
            painter.end()
            return

        w = self.width()
        h = self.height()
        center_y = h * 0.42
        spacing = self.config.active_font_size * 2.4

        for i, (_ts, text) in enumerate(self.lyrics):
            offset = i - self._render_pos
            y = center_y + offset * spacing

            if y < -80 or y > h + 80:
                continue

            is_active = (i == self.current_index)

            if is_active:
                size = self.config.active_font_size
                weight = self.config.active_font_weight
                base_color = QColor(self.config.active_color)
                alpha_f = self.config.active_opacity / 100.0
            else:
                size = self.config.font_size
                weight = self.config.font_weight
                base_color = QColor(self.config.text_color)
                dist = abs(i - self._render_pos)
                fade = max(0.0, 1.0 - max(0.0, dist - 0.6) * 0.28)
                alpha_f = (self.config.text_opacity / 100.0) * fade

            if alpha_f <= 0.01:
                continue

            color = QColor(base_color)
            color.setAlphaF(min(1.0, alpha_f))

            font = QFont()
            font.setPointSize(size)
            font.setWeight(QFont.Weight(max(100, min(900, weight))))
            painter.setFont(font)
            painter.setPen(color)

            fm = painter.fontMetrics()
            x = (w - fm.horizontalAdvance(text)) / 2
            painter.drawText(int(x), int(y + fm.ascent() / 2), text)

        painter.end()

    def _paint_idle(self, painter: QPainter):
        color = QColor("#6b7280")
        color.setAlphaF(0.55)
        painter.setPen(color)
        font = QFont()
        font.setPointSize(13)
        painter.setFont(font)
        msg = self._status
        fm = painter.fontMetrics()
        x = (self.width() - fm.horizontalAdvance(msg)) / 2
        y = self.height() / 2
        painter.drawText(int(x), int(y), msg)
