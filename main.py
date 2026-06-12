import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from config import load_config, save_config
from overlay_window import OverlayWindow


def main():
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("LyricOverlay")
    app.setQuitOnLastWindowClosed(True)

    config = load_config()
    window = OverlayWindow(config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
