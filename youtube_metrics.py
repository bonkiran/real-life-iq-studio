from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from fastapi.responses import JSONResponse

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data"))).resolve()
DB_PATH = DATA_DIR / "studio.db"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _db_connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _ensure_schema(con):
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS youtube_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            comment_id TEXT NOT NULL,
            author TEXT,
            text TEXT,
            like_count INTEGER DEFAULT 0,
            published_at TEXT,
            synced_at TEXT NOT NULL,
            UNIQUE(video_id, comment_id)
        )
        """
    )
    con.commit()


def _extract_video_id(value: str | None) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    if YOUTUBE_VIDEO_ID_RE.fullmatch(raw):
        return raw

    try:
        parsed = urlparse(raw)
    except ValueError:
        return None

    host = parsed.netloc.lower().split(":", 1)[0]
    path_parts = [part for part in parsed.path.split("/") if part]

    if host in {"youtu.be", "www.youtu.be"} and path_parts:
        candidate = path_parts[0]
        return candidate if YOUTUBE_VIDEO_ID_RE.fullmatch(candidate) else None

    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            candidate = (parse_qs(parsed.query).get("v") or [None])[0]
            return candidate if candidate and YOUTUBE_VIDEO_ID_RE.fullmatch(candidate) else None
        if len(path_parts) >= 2 and path_parts[0] in {"shorts", "embed", "live"}:
            candidate = path_parts[1]
            return candidate if YOUTUBE_VIDEO_ID_RE.fullmatch(candidate) else None

    return None


def _api_key() -> str:
    return os.getenv("YOUTUBE_API_KEY", "").strip()


def _youtube_get(endpoint: str, params: dict[str, str | int]) -> dict:
    key = _api_key()
    if not key:
        raise RuntimeError("YOUTUBE_API_KEY is not configured in Render.")

    query = dict(params)
    query["key"] = key
    url = f"{YOUTUBE_API_BASE}/{endpoint}?{urlencode(query)}"
    request = Request(url, headers={"User-Agent": "REAL-LIFE-IQ-Studio/1.0"})
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        message = f"YouTube API returned HTTP {exc.code}."
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            api_message = payload.get("error", {}).get("message")
            if api_message:
                message = api_message
        except Exception:
            pass
        raise RuntimeError(message) from exc
    except URLError as exc:
        raise RuntimeError("Could not reach the YouTube API. Please try again.") from exc


def _fetch_statistics(youtube_video_id: str) -> dict[str, int]:
    payload = _youtube_get(
        "videos",
        {"part": "statistics", "id": youtube_video_id},
    )
    items = payload.get("items") or []
    if not items:
        raise RuntimeError("YouTube could not find that video. Check the YouTube URL and try again.")
    stats = items[0].get("statistics") or {}
    return {
        "views": int(stats.get("viewCount", 0) or 0),
        "likes": int(stats.get("likeCount", 0) or 0),
        "comments": int(stats.get("commentCount", 0) or 0),
    }


def _fetch_recent_comments(youtube_video_id: str, max_results: int = 10) -> tuple[list[dict], str | None]:
    try:
        payload = _youtube_get(
            "commentThreads",
            {
                "part": "snippet",
                "videoId": youtube_video_id,
                "maxResults": max_results,
                "order": "time",
                "textFormat": "plainText",
            },
        )
    except RuntimeError as exc:
        # Metrics should still sync even when comments are disabled or unavailable.
        return [], str(exc)

    comments: list[dict] = []
    for item in payload.get("items") or []:
        top = ((item.get("snippet") or {}).get("topLevelComment") or {})
        snippet = top.get("snippet") or {}
        comment_id = top.get("id") or item.get("id")
        if not comment_id:
            continue
        comments.append(
            {
                "comment_id": comment_id,
                "author": snippet.get("authorDisplayName") or "YouTube user",
                "text": snippet.get("textOriginal") or snippet.get("textDisplay") or "",
                "like_count": int(snippet.get("likeCount", 0) or 0),
                "published_at": snippet.get("publishedAt"),
            }
        )
    return comments, None


def _latest_data(con, video_id: int) -> dict:
    metric = con.execute(
        """SELECT * FROM metrics
           WHERE video_id=? AND notes='YouTube Data API v3 auto-sync'
           ORDER BY id DESC LIMIT 1""",
        (video_id,),
    ).fetchone()
    comments = con.execute(
        """SELECT comment_id, author, text, like_count, published_at, synced_at
           FROM youtube_comments WHERE video_id=?
           ORDER BY COALESCE(published_at, synced_at) DESC LIMIT 10""",
        (video_id,),
    ).fetchall()
    return {
        "metric": dict(metric) if metric else None,
        "comments": [dict(row) for row in comments],
    }


def install_youtube_metrics(app) -> None:
    @app.get("/api/youtube/{video_id}", name="youtube_metrics_status")
    def youtube_metrics_status(video_id: int):
        con = _db_connect()
        try:
            _ensure_schema(con)
            video = con.execute("SELECT id, youtube_url FROM videos WHERE id=?", (video_id,)).fetchone()
            if not video:
                return JSONResponse({"ok": False, "error": "Video record not found."}, status_code=404)
            latest = _latest_data(con, video_id)
            return {
                "ok": True,
                "api_configured": bool(_api_key()),
                "youtube_url": video["youtube_url"],
                "youtube_video_id": _extract_video_id(video["youtube_url"]),
                **latest,
            }
        finally:
            con.close()

    @app.post("/api/youtube/{video_id}/sync", name="youtube_metrics_sync")
    def youtube_metrics_sync(video_id: int):
        con = _db_connect()
        try:
            _ensure_schema(con)
            video = con.execute("SELECT id, youtube_url FROM videos WHERE id=?", (video_id,)).fetchone()
            if not video:
                return JSONResponse({"ok": False, "error": "Video record not found."}, status_code=404)
            if not _api_key():
                return JSONResponse({"ok": False, "error": "YOUTUBE_API_KEY is not configured in Render."}, status_code=503)

            youtube_video_id = _extract_video_id(video["youtube_url"])
            if not youtube_video_id:
                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Paste this Short's YouTube URL under Release details, save the production plan, then sync again.",
                    },
                    status_code=400,
                )

            try:
                stats = _fetch_statistics(youtube_video_id)
                recent_comments, comment_warning = _fetch_recent_comments(youtube_video_id)
            except RuntimeError as exc:
                return JSONResponse({"ok": False, "error": str(exc)}, status_code=502)

            synced_at = datetime.now().isoformat(timespec="seconds")
            con.execute(
                """INSERT INTO metrics(video_id,captured_at,views,likes,comments,subscribers,
                                       avg_view_duration,avg_percent_viewed,viewed_vs_swiped,notes)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    video_id,
                    synced_at,
                    stats["views"],
                    stats["likes"],
                    stats["comments"],
                    0,
                    None,
                    None,
                    None,
                    "YouTube Data API v3 auto-sync",
                ),
            )

            con.execute("DELETE FROM youtube_comments WHERE video_id=?", (video_id,))
            for comment in recent_comments:
                con.execute(
                    """INSERT INTO youtube_comments(video_id,comment_id,author,text,like_count,published_at,synced_at)
                       VALUES(?,?,?,?,?,?,?)""",
                    (
                        video_id,
                        comment["comment_id"],
                        comment["author"],
                        comment["text"],
                        comment["like_count"],
                        comment["published_at"],
                        synced_at,
                    ),
                )
            con.commit()

            latest = _latest_data(con, video_id)
            return {
                "ok": True,
                "youtube_video_id": youtube_video_id,
                "comment_warning": comment_warning,
                **latest,
            }
        finally:
            con.close()
