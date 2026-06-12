import json
from pathlib import Path
from dataclasses import dataclass, asdict

CONFIG_DIR = Path.home() / ".lyricoverlay"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class Config:
    # Spotify OAuth
    spotify_client_id: str = ""
    spotify_client_secret: str = ""

    # Window
    always_on_top: bool = True
    window_opacity: int = 70        # 1-100 %
    bg_color: str = "#111827"
    window_width: int = 460
    window_height: int = 520
    window_x: int = 60
    window_y: int = 60

    # Regular lyric lines
    text_color: str = "#9ca3af"
    text_opacity: int = 90          # 0-100 %
    font_size: int = 15
    font_weight: int = 400          # 100-900

    # Active (current) line
    active_color: str = "#fbbf24"
    active_opacity: int = 100       # 0-100 %
    active_font_size: int = 19
    active_font_weight: int = 700

    # Source
    source: str = "spotify"             # "spotify" | "ytmusic"

    # Hotkeys
    clickthrough_hotkey: str = "ctrl+shift+c"


def load_config() -> Config:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            c = Config()
            for k, v in data.items():
                if hasattr(c, k):
                    setattr(c, k, v)
            return c
        except Exception:
            pass
    return Config()


def save_config(config: Config) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(asdict(config), f, indent=2)
