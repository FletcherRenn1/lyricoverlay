# LyricOverlay

A Windows overlay that shows synced lyrics for whatever you're listening to, sitting on top of any application (games, video, etc). Supports Spotify and YouTube Music.
I made this because i was annoyed by the fact that most usable options were locked behind subscriptions and paywalls, aswell as very questionable practices behind those.

![Windows 10/11](https://img.shields.io/badge/Windows-10%2F11-blue)

## Features

- Always-on-top frameless window with adjustable opacity
- Line-by-line synced lyrics from [LRCLIB](https://lrclib.net)
- Spotify and YouTube Music support
- Click-through toggle via hotkey — overlay becomes fully transparent and mouse events pass through to whatever is behind it
- Resizable and draggable
- Lyrics cached locally so revisited tracks load instantly
- Configurable font size, weight, and opacity for active and inactive lines

## Getting started

### Option 1 — Standalone executable (recommended)

Download `LyricOverlay.exe` from the [latest release](https://github.com/FletcherRenn1/lyricoverlay/releases/latest) and run it. No Python or any other software required.

> Windows Defender may flag the .exe as suspicious. This is a known false positive with self-contained Python executables. You can verify the source code in this repo.

### Option 2 — Run from source

Requires Python 3.11+.

```
pip install -r requirements.txt
python main.py
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

## License

GNU General Public License v3.0
