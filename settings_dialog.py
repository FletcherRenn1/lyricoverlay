from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QPushButton, QSlider,
    QSpinBox, QCheckBox, QDialogButtonBox, QGroupBox, QComboBox,
)
from PyQt6.QtCore import Qt

from config import Config


def _slider(lo: int, hi: int, val: int, step: int = 1) -> tuple[QSlider, QLabel]:
    s = QSlider(Qt.Orientation.Horizontal)
    s.setRange(lo, hi)
    s.setSingleStep(step)
    s.setPageStep(step * 10)
    s.setValue(val)
    lbl = QLabel(str(val))
    lbl.setFixedWidth(36)
    s.valueChanged.connect(lambda v: lbl.setText(str(v)))
    return s, lbl


class SettingsDialog(QDialog):
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("LyricOverlay — Settings")
        self.setMinimumWidth(460)
        self.setModal(True)

        root = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._source_tab(), "Source")
        tabs.addTab(self._spotify_tab(), "Spotify")
        tabs.addTab(self._appearance_tab(), "Appearance")
        tabs.addTab(self._text_tab(), "Text / Font")
        tabs.addTab(self._hotkeys_tab(), "Hotkeys")
        root.addWidget(tabs)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

        self._apply_dark()

    def _source_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        info = QLabel(
            "<b>Spotify</b> — requires credentials and OAuth login (see the Spotify tab).<br><br>"
            "<b>YouTube Music</b> — reads whatever is playing in your browser via Windows media "
            "session. No setup needed; just play something on YouTube Music in Chrome/Edge/Firefox."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#9ca3af;font-size:12px;padding:8px;background:#1f2937;"
                           "border-radius:6px")
        layout.addWidget(info)

        form = QFormLayout()
        self._source_combo = QComboBox()
        self._source_combo.addItem("Spotify", "spotify")
        self._source_combo.addItem("YouTube Music", "ytmusic")
        idx = self._source_combo.findData(self.config.source)
        if idx >= 0:
            self._source_combo.setCurrentIndex(idx)
        form.addRow("Music source:", self._source_combo)
        layout.addLayout(form)

        layout.addStretch()
        return w

    def _spotify_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        info = QLabel(
            "<b>Create a Spotify app:</b><br>"
            "1. Go to <a href='https://developer.spotify.com/dashboard'>developer.spotify.com/dashboard</a><br>"
            "2. Create an app (any name/description)<br>"
            "3. In app settings add redirect URI: <code>http://127.0.0.1:8888/callback</code><br>"
            "4. Copy Client ID and Client Secret below"
        )
        info.setWordWrap(True)
        info.setOpenExternalLinks(True)
        info.setStyleSheet("color:#9ca3af;font-size:12px;padding:8px;background:#1f2937;"
                           "border-radius:6px")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(8)

        self._cid = QLineEdit(self.config.spotify_client_id)
        self._cid.setPlaceholderText("Paste Client ID…")
        form.addRow("Client ID:", self._cid)

        self._csec = QLineEdit(self.config.spotify_client_secret)
        self._csec.setEchoMode(QLineEdit.EchoMode.Password)
        self._csec.setPlaceholderText("Paste Client Secret…")
        form.addRow("Client Secret:", self._csec)

        layout.addLayout(form)

        auth_row = QHBoxLayout()
        self._auth_btn = QPushButton("Connect / Re-authenticate")
        self._auth_btn.clicked.connect(self._do_oauth)
        auth_row.addWidget(self._auth_btn)

        self._auth_status = QLabel("")
        auth_row.addWidget(self._auth_status)
        layout.addLayout(auth_row)

        layout.addStretch()
        return w

    def _appearance_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)

        self._win_op, win_op_lbl = _slider(1, 100, self.config.window_opacity)
        op_row = QHBoxLayout()
        op_row.addWidget(QLabel("Window opacity:"))
        op_row.addWidget(self._win_op)
        op_row.addWidget(win_op_lbl)
        op_row.addWidget(QLabel("%"))
        layout.addLayout(op_row)

        self._aot = QCheckBox("Always on top")
        self._aot.setChecked(self.config.always_on_top)
        layout.addWidget(self._aot)

        layout.addStretch()
        return w

    def _text_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)

        grp1 = QGroupBox("Regular lines")
        f1 = QFormLayout(grp1)

        self._txt_op, txt_op_lbl = _slider(0, 100, self.config.text_opacity)
        op_w = QWidget()
        op_l = QHBoxLayout(op_w)
        op_l.setContentsMargins(0, 0, 0, 0)
        op_l.addWidget(self._txt_op)
        op_l.addWidget(txt_op_lbl)
        op_l.addWidget(QLabel("%"))
        f1.addRow("Opacity:", op_w)

        self._font_size = QSpinBox()
        self._font_size.setRange(8, 72)
        self._font_size.setValue(self.config.font_size)
        f1.addRow("Font size:", self._font_size)

        self._font_wt, fw_lbl = _slider(100, 900, self.config.font_weight, step=100)
        fw_w = QWidget()
        fw_l = QHBoxLayout(fw_w)
        fw_l.setContentsMargins(0, 0, 0, 0)
        fw_l.addWidget(self._font_wt)
        fw_l.addWidget(fw_lbl)
        f1.addRow("Weight:", fw_w)

        layout.addWidget(grp1)

        grp2 = QGroupBox("Active (current) line")
        f2 = QFormLayout(grp2)

        self._act_op, act_op_lbl = _slider(0, 100, self.config.active_opacity)
        aop_w = QWidget()
        aop_l = QHBoxLayout(aop_w)
        aop_l.setContentsMargins(0, 0, 0, 0)
        aop_l.addWidget(self._act_op)
        aop_l.addWidget(act_op_lbl)
        aop_l.addWidget(QLabel("%"))
        f2.addRow("Opacity:", aop_w)

        self._act_size = QSpinBox()
        self._act_size.setRange(8, 72)
        self._act_size.setValue(self.config.active_font_size)
        f2.addRow("Font size:", self._act_size)

        self._act_wt, awt_lbl = _slider(100, 900, self.config.active_font_weight, step=100)
        awt_w = QWidget()
        awt_l = QHBoxLayout(awt_w)
        awt_l.setContentsMargins(0, 0, 0, 0)
        awt_l.addWidget(self._act_wt)
        awt_l.addWidget(awt_lbl)
        f2.addRow("Weight:", awt_w)

        layout.addWidget(grp2)
        layout.addStretch()
        return w

    def _hotkeys_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)

        info = QLabel(
            "Use modifier+key format, e.g. <code>ctrl+shift+c</code> or <code>alt+l</code>.<br>"
            "The hotkey works even when click-through is active."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#9ca3af;font-size:12px")
        layout.addWidget(info)

        form = QFormLayout()
        self._ct_hotkey = QLineEdit(self.config.clickthrough_hotkey)
        form.addRow("Toggle click-through:", self._ct_hotkey)
        layout.addLayout(form)

        layout.addStretch()
        return w

    def _do_oauth(self):
        from spotify_client import SpotifyClient
        cid = self._cid.text().strip()
        csec = self._csec.text().strip()
        if not cid or not csec:
            self._auth_status.setText("⚠ Fill in credentials first")
            return

        self._auth_btn.setEnabled(False)
        self._auth_status.setText("Opening browser…")

        client = SpotifyClient(cid, csec)

        def on_ok():
            self._auth_status.setText("✓ Connected!")
            self._auth_btn.setEnabled(True)

        def on_err(msg: str):
            self._auth_status.setText(f"✗ {msg}")
            self._auth_btn.setEnabled(True)

        client.start_oauth(on_ok, on_err)

    def _accept(self):
        c = self.config
        c.source = self._source_combo.currentData()
        c.spotify_client_id = self._cid.text().strip()
        c.spotify_client_secret = self._csec.text().strip()
        c.window_opacity = self._win_op.value()
        c.always_on_top = self._aot.isChecked()
        c.text_opacity = self._txt_op.value()
        c.font_size = self._font_size.value()
        c.font_weight = self._font_wt.value()
        c.active_opacity = self._act_op.value()
        c.active_font_size = self._act_size.value()
        c.active_font_weight = self._act_wt.value()
        c.clickthrough_hotkey = self._ct_hotkey.text().strip() or "ctrl+shift+c"
        self.accept()

    def _apply_dark(self):
        self.setStyleSheet("""
            QDialog, QTabWidget, QWidget {
                background:#111827; color:#e5e7eb;
            }
            QTabBar::tab {
                background:#1f2937; color:#9ca3af;
                padding:6px 14px; border-radius:4px 4px 0 0;
            }
            QTabBar::tab:selected { background:#374151; color:#f3f4f6; }
            QGroupBox {
                border:1px solid #374151; border-radius:6px;
                margin-top:8px; padding-top:8px;
                color:#9ca3af; font-size:11px;
            }
            QGroupBox::title { subcontrol-origin:margin; left:10px; }
            QLineEdit, QSpinBox {
                background:#1f2937; border:1px solid #374151;
                border-radius:4px; padding:4px 6px; color:#e5e7eb;
            }
            QSlider::groove:horizontal { height:4px; background:#374151; border-radius:2px; }
            QSlider::handle:horizontal {
                width:14px; height:14px; margin:-5px 0;
                background:#6366f1; border-radius:7px;
            }
            QCheckBox { color:#e5e7eb; }
            QPushButton {
                background:#374151; color:#e5e7eb; border:none;
                border-radius:5px; padding:5px 12px;
            }
            QPushButton:hover { background:#4b5563; }
            QDialogButtonBox QPushButton { min-width:80px; }
            QComboBox {
                background:#1f2937; border:1px solid #374151;
                border-radius:4px; padding:4px 6px; color:#e5e7eb;
            }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView {
                background:#1f2937; color:#e5e7eb; selection-background-color:#374151;
            }
        """)
