import asyncio
from datetime import timedelta
from typing import Optional


def get_current_playback() -> Optional[dict]:
    try:
        return asyncio.run(_fetch())
    except Exception as exc:
        print(f"[SMTC] {exc}")
        return None


async def _fetch() -> Optional[dict]:
    from winrt.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as Manager,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
    )

    manager = await Manager.request_async()
    sessions = manager.get_sessions()

    best = None
    for session in sessions:
        app_id = (session.source_app_user_model_id or "").lower()
        is_browser = any(b in app_id for b in ("chrome", "firefox", "msedge", "opera", "brave"))
        if is_browser:
            best = session
            break

    if best is None:
        return None

    try:
        info = await best.try_get_media_properties_async()
        timeline = best.get_timeline_properties()
        pb_info = best.get_playback_info()
    except Exception:
        return None

    if info is None or pb_info.playback_status != PlaybackStatus.PLAYING:
        return None

    track_name = info.title or ""
    artist = info.artist or ""

    if not track_name:
        return None

    def _td_to_ms(td: timedelta) -> int:
        return int(td.total_seconds() * 1000)

    return {
        "track_name": track_name,
        "artist": artist,
        "album": info.album_title or "",
        "progress_ms": _td_to_ms(timeline.position),
        "duration_ms": _td_to_ms(timeline.end_time),
        "track_id": f"yt:{track_name}:{artist}",
        "is_playing": True,
    }
