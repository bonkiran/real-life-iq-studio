from __future__ import annotations

import base64
import hashlib
import hmac
import html
import json
import os
import secrets
import sqlite3
import time
from datetime import date, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request as UrlRequest, urlopen

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data"))).resolve()
DB_PATH = DATA_DIR / "studio.db"

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
ANALYTICS_URL = "https://youtubeanalytics.googleapis.com/v2/reports"
YOUTUBE_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def _db_connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _ensure_schema(con):
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS youtube_oauth (
            id INTEGER PRIMARY KEY CHECK(id=1),
            refresh_token TEXT,
            access_token TEXT,
            expires_at INTEGER,
            channel_id TEXT,
            channel_title TEXT,
            scope TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS youtube_analytics_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            captured_at TEXT NOT NULL,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            engaged_views INTEGER DEFAULT 0,
            estimated_minutes_watched REAL DEFAULT 0,
            average_view_duration REAL,
            average_view_percentage REAL,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            subscribers_gained INTEGER DEFAULT 0,
            subscribers_lost INTEGER DEFAULT 0
        );
        """
    )
    con.commit()


def _client_id() -> str:
    return os.getenv("YOUTUBE_OAUTH_CLIENT_ID", "").strip()


def _client_secret() -> str:
    return os.getenv("YOUTUBE_OAUTH_CLIENT_SECRET", "").strip()


def _env_refresh_token() -> str:
    return os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip()


def _oauth_configured() -> bool:
    return bool(_client_id() and _client_secret())


def _state_secret() -> bytes:
    material = (os.getenv("STUDIO_PASSWORD", "") + "\0" + _client_secret()).encode("utf-8")
    return hashlib.sha256(material).digest()


def _make_state(video_id: int | None) -> str:
    stamp = int(time.time())
    nonce = secrets.token_urlsafe(12)
    payload = f"{stamp}|{nonce}|{video_id or 0}"
    sig = hmac.new(_state_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    raw = f"{payload}|{sig}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _parse_state(state: str) -> int | None:
    try:
        padded = state + "=" * (-len(state) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        stamp_text, nonce, video_text, sig = raw.split("|", 3)
        payload = f"{stamp_text}|{nonce}|{video_text}"
        expected = hmac.new(_state_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(time.time()) - int(stamp_text) > 15 * 60:
            return None
        value = int(video_text)
        return value if value > 0 else 0
    except Exception:
        return None


def _redirect_uri(request: Request) -> str:
    configured = os.getenv("YOUTUBE_OAUTH_REDIRECT_URI", "").strip()
    if configured:
        return configured
    return str(request.url_for("youtube_oauth_callback"))


def _post_form(url: str, data: dict[str, str]) -> dict:
    encoded = urlencode(data).encode("utf-8")
    req = UrlRequest(
        url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "REAL-LIFE-IQ-Studio/2.0"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        message = f"Google OAuth returned HTTP {exc.code}."
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            message = payload.get("error_description") or payload.get("error", {}).get("message") or payload.get("error") or message
        except Exception:
            pass
        raise RuntimeError(str(message)) from exc
    except URLError as exc:
        raise RuntimeError("Could not reach Google OAuth. Please try again.") from exc


def _bearer_get(url: str, access_token: str, params: dict[str, str] | None = None) -> dict:
    if params:
        url = f"{url}?{urlencode(params)}"
    req = UrlRequest(
        url,
        headers={"Authorization": f"Bearer {access_token}", "User-Agent": "REAL-LIFE-IQ-Studio/2.0"},
    )
    try:
        with urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        message = f"YouTube Analytics returned HTTP {exc.code}."
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            message = payload.get("error", {}).get("message") or message
        except Exception:
            pass
        raise RuntimeError(message) from exc
    except URLError as exc:
        raise RuntimeError("Could not reach YouTube Analytics. Please try again.") from exc


def _stored_oauth(con):
    _ensure_schema(con)
    return con.execute("SELECT * FROM youtube_oauth WHERE id=1").fetchone()


def _refresh_token(con) -> str:
    env_token = _env_refresh_token()
    if env_token:
        return env_token
    row = _stored_oauth(con)
    return (row["refresh_token"] or "").strip() if row else ""


def _access_token(con) -> str:
    if not _oauth_configured():
        raise RuntimeError("YouTube OAuth client is not configured in Render.")

    row = _stored_oauth(con)
    now = int(time.time())
    if row and row["access_token"] and int(row["expires_at"] or 0) > now + 90:
        return row["access_token"]

    refresh = _refresh_token(con)
    if not refresh:
        raise RuntimeError("YouTube Analytics is not connected yet. Connect the REAL-LIFE IQ YouTube channel first.")

    payload = _post_form(
        TOKEN_URL,
        {
            "client_id": _client_id(),
            "client_secret": _client_secret(),
            "refresh_token": refresh,
            "grant_type": "refresh_token",
        },
    )
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("Google did not return an access token. Reconnect YouTube Analytics.")
    expires_at = now + int(payload.get("expires_in", 3600))

    existing = row
    con.execute(
        """INSERT INTO youtube_oauth(id,refresh_token,access_token,expires_at,channel_id,channel_title,scope,updated_at)
           VALUES(1,?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET
             refresh_token=COALESCE(excluded.refresh_token,youtube_oauth.refresh_token),
             access_token=excluded.access_token,
             expires_at=excluded.expires_at,
             channel_id=COALESCE(excluded.channel_id,youtube_oauth.channel_id),
             channel_title=COALESCE(excluded.channel_title,youtube_oauth.channel_title),
             scope=COALESCE(excluded.scope,youtube_oauth.scope),
             updated_at=excluded.updated_at""",
        (
            None if _env_refresh_token() else refresh,
            token,
            expires_at,
            existing["channel_id"] if existing else None,
            existing["channel_title"] if existing else None,
            payload.get("scope") or (existing["scope"] if existing else None),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    con.commit()
    return token


def _channel_info(access_token: str) -> tuple[str | None, str | None]:
    payload = _bearer_get(
        YOUTUBE_CHANNELS_URL,
        access_token,
        {"part": "id,snippet", "mine": "true", "maxResults": "1"},
    )
    items = payload.get("items") or []
    if not items:
        return None, None
    item = items[0]
    return item.get("id"), (item.get("snippet") or {}).get("title")


def _extract_video_id(value: str | None) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    if len(raw) == 11 and all(ch.isalnum() or ch in "_-" for ch in raw):
        return raw
    try:
        parsed = urlparse(raw)
    except ValueError:
        return None
    host = parsed.netloc.lower().split(":", 1)[0]
    parts = [p for p in parsed.path.split("/") if p]
    if host in {"youtu.be", "www.youtu.be"} and parts:
        return parts[0] if len(parts[0]) == 11 else None
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            candidate = (parse_qs(parsed.query).get("v") or [None])[0]
            return candidate if candidate and len(candidate) == 11 else None
        if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"}:
            return parts[1] if len(parts[1]) == 11 else None
    return None


def _query_video_analytics(access_token: str, youtube_video_id: str, start_date: str, end_date: str) -> dict:
    metrics = [
        "views",
        "engagedViews",
        "estimatedMinutesWatched",
        "averageViewDuration",
        "averageViewPercentage",
        "likes",
        "comments",
        "shares",
        "subscribersGained",
        "subscribersLost",
    ]
    payload = _bearer_get(
        ANALYTICS_URL,
        access_token,
        {
            "ids": "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": ",".join(metrics),
            "filters": f"video=={youtube_video_id}",
        },
    )
    headers = [col.get("name") for col in payload.get("columnHeaders") or []]
    rows = payload.get("rows") or []
    values = rows[0] if rows else [0] * len(headers)
    data = dict(zip(headers, values))
    return {
        "views": int(data.get("views", 0) or 0),
        "engaged_views": int(data.get("engagedViews", 0) or 0),
        "estimated_minutes_watched": float(data.get("estimatedMinutesWatched", 0) or 0),
        "average_view_duration": float(data["averageViewDuration"]) if data.get("averageViewDuration") is not None else None,
        "average_view_percentage": float(data["averageViewPercentage"]) if data.get("averageViewPercentage") is not None else None,
        "likes": int(data.get("likes", 0) or 0),
        "comments": int(data.get("comments", 0) or 0),
        "shares": int(data.get("shares", 0) or 0),
        "subscribers_gained": int(data.get("subscribersGained", 0) or 0),
        "subscribers_lost": int(data.get("subscribersLost", 0) or 0),
    }


def _latest_snapshot(con, video_id: int):
    row = con.execute(
        "SELECT * FROM youtube_analytics_snapshots WHERE video_id=? ORDER BY id DESC LIMIT 1",
        (video_id,),
    ).fetchone()
    return dict(row) if row else None


def install_youtube_analytics(app) -> None:
    @app.get("/youtube/oauth/connect", name="youtube_oauth_connect")
    def youtube_oauth_connect(request: Request, video_id: int = 0):
        if not _oauth_configured():
            return HTMLResponse(
                "YouTube OAuth is not configured. Add YOUTUBE_OAUTH_CLIENT_ID and YOUTUBE_OAUTH_CLIENT_SECRET in Render first.",
                status_code=503,
            )
        redirect_uri = _redirect_uri(request)
        params = {
            "client_id": _client_id(),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": _make_state(video_id),
        }
        return RedirectResponse(f"{AUTH_URL}?{urlencode(params)}", status_code=302)

    @app.get("/youtube/oauth/callback", name="youtube_oauth_callback")
    def youtube_oauth_callback(request: Request, code: str = "", state: str = "", error: str = ""):
        video_id = _parse_state(state)
        if video_id is None:
            return HTMLResponse("Invalid or expired OAuth state. Return to the Studio and try Connect again.", status_code=400)
        if error:
            return HTMLResponse(f"Google authorization was not completed: {html.escape(error)}", status_code=400)
        if not code:
            return HTMLResponse("Google did not return an authorization code.", status_code=400)

        try:
            payload = _post_form(
                TOKEN_URL,
                {
                    "code": code,
                    "client_id": _client_id(),
                    "client_secret": _client_secret(),
                    "redirect_uri": _redirect_uri(request),
                    "grant_type": "authorization_code",
                },
            )
            access_token = payload.get("access_token")
            if not access_token:
                raise RuntimeError("Google did not return an access token.")
            refresh_token = payload.get("refresh_token")
            channel_id, channel_title = _channel_info(access_token)

            con = _db_connect()
            try:
                _ensure_schema(con)
                existing = con.execute("SELECT * FROM youtube_oauth WHERE id=1").fetchone()
                refresh_to_store = refresh_token or (existing["refresh_token"] if existing else None)
                con.execute(
                    """INSERT INTO youtube_oauth(id,refresh_token,access_token,expires_at,channel_id,channel_title,scope,updated_at)
                       VALUES(1,?,?,?,?,?,?,?)
                       ON CONFLICT(id) DO UPDATE SET
                         refresh_token=COALESCE(excluded.refresh_token,youtube_oauth.refresh_token),
                         access_token=excluded.access_token,
                         expires_at=excluded.expires_at,
                         channel_id=excluded.channel_id,
                         channel_title=excluded.channel_title,
                         scope=excluded.scope,
                         updated_at=excluded.updated_at""",
                    (
                        refresh_to_store,
                        access_token,
                        int(time.time()) + int(payload.get("expires_in", 3600)),
                        channel_id,
                        channel_title,
                        payload.get("scope"),
                        datetime.now().isoformat(timespec="seconds"),
                    ),
                )
                con.commit()
            finally:
                con.close()
        except RuntimeError as exc:
            return HTMLResponse(f"YouTube connection failed: {html.escape(str(exc))}", status_code=502)

        back_path = f"/videos/{video_id}" if video_id else "/videos"
        token_block = ""
        if refresh_token and not _env_refresh_token():
            token_block = f"""
            <div class='secret'>
              <strong>One-time persistence step</strong>
              <p>Copy this refresh token into Render as <code>YOUTUBE_REFRESH_TOKEN</code>. Do not share it or put it in GitHub.</p>
              <textarea readonly onclick='this.select()'>{html.escape(refresh_token)}</textarea>
            </div>
            """

        page = f"""
        <!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
        <title>REAL-LIFE IQ — YouTube Connected</title>
        <style>body{{margin:0;background:#0b1f33;color:#e9f2f9;font-family:Inter,system-ui,Segoe UI,Arial,sans-serif;display:grid;place-items:center;min-height:100vh}}.box{{width:min(720px,90vw);background:#102a43;border:1px solid #28516f;border-radius:18px;padding:32px;box-shadow:0 20px 60px rgba(0,0,0,.3)}}h1{{margin-top:0}}p{{color:#c4d5e3;line-height:1.55}}code{{background:#071726;padding:3px 7px;border-radius:5px;color:#ffd477}}textarea{{width:100%;height:110px;background:#071726;color:#e9f2f9;border:1px solid #3d6684;border-radius:8px;padding:10px;box-sizing:border-box}}a{{display:inline-block;margin-top:18px;background:#ffd166;color:#102a43;padding:10px 16px;border-radius:8px;text-decoration:none;font-weight:700}}.secret{{margin-top:18px;padding:18px;border:1px solid #d8a83e;border-radius:12px;background:#182f43}}</style></head>
        <body><div class='box'><h1>YouTube Analytics connected</h1><p>Connected channel: <strong>{html.escape(channel_title or channel_id or 'YouTube channel')}</strong></p>{token_block}<a href='{back_path}'>Return to REAL-LIFE IQ Studio</a></div></body></html>
        """
        response = HTMLResponse(page)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/youtube-analytics/status", name="youtube_analytics_status")
    def youtube_analytics_status(video_id: int = 0):
        con = _db_connect()
        try:
            _ensure_schema(con)
            row = _stored_oauth(con)
            connected = bool(_refresh_token(con))
            latest = _latest_snapshot(con, video_id) if video_id else None
            return {
                "ok": True,
                "client_configured": _oauth_configured(),
                "connected": connected,
                "persistent": bool(_env_refresh_token()),
                "channel_id": row["channel_id"] if row else None,
                "channel_title": row["channel_title"] if row else None,
                "latest": latest,
            }
        finally:
            con.close()

    @app.post("/api/youtube-analytics/{video_id}/sync", name="youtube_analytics_sync")
    def youtube_analytics_sync(video_id: int):
        con = _db_connect()
        try:
            _ensure_schema(con)
            video = con.execute(
                "SELECT id,youtube_url,publish_date,upload_date FROM videos WHERE id=?",
                (video_id,),
            ).fetchone()
            if not video:
                return JSONResponse({"ok": False, "error": "Video record not found."}, status_code=404)
            youtube_video_id = _extract_video_id(video["youtube_url"])
            if not youtube_video_id:
                return JSONResponse({"ok": False, "error": "Save the published YouTube URL first."}, status_code=400)

            try:
                token = _access_token(con)
                start_date = video["publish_date"] or video["upload_date"] or "2005-01-01"
                end_date = date.today().isoformat()
                analytics = _query_video_analytics(token, youtube_video_id, start_date, end_date)
            except RuntimeError as exc:
                return JSONResponse({"ok": False, "error": str(exc)}, status_code=502)

            captured_at = datetime.now().isoformat(timespec="seconds")
            con.execute(
                """INSERT INTO youtube_analytics_snapshots(
                       video_id,captured_at,period_start,period_end,views,engaged_views,
                       estimated_minutes_watched,average_view_duration,average_view_percentage,
                       likes,comments,shares,subscribers_gained,subscribers_lost)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    video_id,
                    captured_at,
                    start_date,
                    end_date,
                    analytics["views"],
                    analytics["engaged_views"],
                    analytics["estimated_minutes_watched"],
                    analytics["average_view_duration"],
                    analytics["average_view_percentage"],
                    analytics["likes"],
                    analytics["comments"],
                    analytics["shares"],
                    analytics["subscribers_gained"],
                    analytics["subscribers_lost"],
                ),
            )
            con.execute(
                """INSERT INTO metrics(video_id,captured_at,views,likes,comments,subscribers,
                                       avg_view_duration,avg_percent_viewed,viewed_vs_swiped,notes)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    video_id,
                    captured_at,
                    analytics["views"],
                    analytics["likes"],
                    analytics["comments"],
                    analytics["subscribers_gained"],
                    analytics["average_view_duration"],
                    analytics["average_view_percentage"],
                    None,
                    "YouTube Analytics API v2 auto-sync",
                ),
            )
            con.commit()
            return {
                "ok": True,
                "youtube_video_id": youtube_video_id,
                "latest": _latest_snapshot(con, video_id),
            }
        finally:
            con.close()
