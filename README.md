# LyricOverlay

A Windows overlay that shows synced lyrics for whatever you're listening to, sitting on top of any application (games, video, etc). Supports Spotify and YouTube Music.

![Windows 10/11](https://img.shields.io/badge/Windows-10%2F11-blue)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)

## Features

- Always-on-top frameless window with adjustable opacity
- Line-by-line synced lyrics from [LRCLIB](https://lrclib.net)
- Spotify and YouTube Music support
- Click-through toggle via hotkey — overlay becomes fully transparent and mouse events pass through to whatever is behind it
- Resizable and draggable
- Lyrics cached locally so revisited tracks load instantly
- Configurable font size, weight, and opacity for active and inactive lines

## Requirements

- Windows 10 or 11
- Python 3.11+

## Running from source

**1. Install dependencies**

```
pip install -r requirements.txt
```

**2. Run**

```
python main.py
```

**3. Optional — create a desktop shortcut**

```
python create_shortcut.py
```

## Spotify setup

LyricOverlay uses the Spotify Web API, which requires a free developer app:

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) and create an app (any name)
2. In the app settings, add `http://127.0.0.1:8888/callback` as a Redirect URI
3. Copy the **Client ID** and **Client Secret**
4. Open LyricOverlay, click the settings icon, go to the **Spotify** tab, paste the credentials, and click **Connect**

## YouTube Music setup

No setup required. Switch to YouTube Music in **Settings → Source**, then play something in Chrome, Edge, or Firefox. The overlay reads the track from Windows media session — the same thing that shows up in the taskbar media controls.

## Hotkeys

| Action | Default |
|---|---|
| Toggle click-through | `Ctrl+Shift+C` |

The hotkey can be changed in **Settings → Hotkeys**. It works even when click-through is active.

## Building a standalone .exe

Install PyInstaller:

```
pip install pyinstaller
```

Build:

```
pyinstaller --onefile --noconsole --name LyricOverlay --collect-all winrt main.py
```

The output will be at `dist/LyricOverlay.exe`. Note that Windows Defender or other antivirus may flag unsigned PyInstaller executables as suspicious — this is a known false positive with PyInstaller.

## License

MIT
