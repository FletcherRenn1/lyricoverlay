import re
from typing import Optional
import requests

LRCLIB_GET    = "https://lrclib.net/api/get"
LRCLIB_SEARCH = "https://lrclib.net/api/search"

LyricLine = tuple[float, str]


def fetch_lyrics(
    track_name: str,
    artist: str,
    album: str = "",
    duration_ms: int = 0,
) -> Optional[list[LyricLine]]:
    result = _get_exact(track_name, artist, album, duration_ms)
    if result:
        return result
    return _search_fallback(track_name, artist, duration_ms)


def _get_exact(
    track_name: str,
    artist: str,
    album: str,
    duration_ms: int,
) -> Optional[list[LyricLine]]:
    params: dict = {"track_name": track_name, "artist_name": artist}
    if album:
        params["album_name"] = album
    if duration_ms > 0:
        params["duration"] = duration_ms // 1000
    try:
        resp = requests.get(LRCLIB_GET, params=params, timeout=10)
        if resp.status_code == 200:
            return _extract(resp.json(), duration_ms)
    except Exception as exc:
        print(f"[Lyrics/get] {exc}")
    return None


def _search_fallback(
    track_name: str,
    artist: str,
    duration_ms: int,
) -> Optional[list[LyricLine]]:
    try:
        resp = requests.get(
            LRCLIB_SEARCH,
            params={"track_name": track_name, "artist_name": artist},
            timeout=10,
        )
        if resp.status_code == 200:
            results = resp.json()
            if isinstance(results, list):
                for item in results:
                    lines = _extract(item, duration_ms)
                    if lines:
                        return lines
    except Exception as exc:
        print(f"[Lyrics/search] {exc}")
    return None


def _extract(data: dict, duration_ms: int) -> Optional[list[LyricLine]]:
    if data.get("syncedLyrics"):
        lines = _parse_lrc(data["syncedLyrics"])
        if lines:
            return lines
    if data.get("plainLyrics"):
        raw = [l for l in data["plainLyrics"].splitlines() if l.strip()]
        if raw:
            secs = (duration_ms / 1000) if duration_ms else len(raw) * 3.5
            step = secs / max(len(raw), 1)
            return [(i * step, line) for i, line in enumerate(raw)]
    return None


def _parse_lrc(text: str) -> list[LyricLine]:
    pat = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\](.*)")
    result: list[LyricLine] = []
    for line in text.splitlines():
        m = pat.match(line.strip())
        if m:
            ts = int(m.group(1)) * 60 + float(m.group(2))
            content = m.group(3).strip()
            result.append((ts, content))
    return sorted(result, key=lambda x: x[0])


def current_line_index(lyrics: list[LyricLine], progress_s: float) -> int:
    idx = 0
    for i, (ts, _) in enumerate(lyrics):
        if ts <= progress_s:
            idx = i
        else:
            break
    return idx
