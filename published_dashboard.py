from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime

from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse

BASE_DIR = Path(__file__).resolve().parent
SEED_PATH = BASE_DIR / "seed" / "published_channels.json"


def ensure_published_catalog(con: sqlite3.Connection) -> None:
    con.execute(
        """CREATE TABLE IF NOT EXISTS published_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_slug TEXT NOT NULL,
            channel_name TEXT NOT NULL,
            sequence_no INTEGER NOT NULL,
            title TEXT NOT NULL,
            publish_date TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(channel_slug, sequence_no)
        )"""
    )

    if SEED_PATH.exists():
        payload = json.loads(SEED_PATH.read_text(encoding="utf-8"))
        now = datetime.now().isoformat(timespec="seconds")
        for channel in payload.get("channels", []):
            slug = (channel.get("slug") or "").strip()
            name = (channel.get("name") or slug).strip()
            if not slug:
                continue
            for video in channel.get("videos", []):
                con.execute(
                    """INSERT INTO published_catalog(
                           channel_slug,channel_name,sequence_no,title,publish_date,updated_at
                       ) VALUES(?,?,?,?,?,?)
                       ON CONFLICT(channel_slug,sequence_no) DO UPDATE SET
                           channel_name=excluded.channel_name,
                           title=excluded.title,
                           publish_date=excluded.publish_date,
                           updated_at=excluded.updated_at""",
                    (
                        slug,
                        name,
                        int(video["sequence_no"]),
                        video["title"],
                        video["publish_date"],
                        now,
                    ),
                )

        # Keep channel records available in the main Channels area too.
        con.execute(
            """CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                handle TEXT,
                status TEXT NOT NULL DEFAULT 'Incubator',
                mission TEXT,
                tagline TEXT,
                audience TEXT,
                content_pillars TEXT,
                format_strategy TEXT,
                language_strategy TEXT,
                visual_style TEXT,
                source_policy TEXT,
                notes TEXT,
                youtube_channel_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )
        for channel in payload.get("channels", []):
            slug = (channel.get("slug") or "").strip()
            name = (channel.get("name") or slug).strip()
            if not slug:
                continue
            existing = con.execute("SELECT id FROM channels WHERE slug=?", (slug,)).fetchone()
            if existing:
                con.execute("UPDATE channels SET name=?,updated_at=? WHERE slug=?", (name, now, slug))
            else:
                con.execute(
                    "INSERT INTO channels(slug,name,status,created_at,updated_at) VALUES(?,?,?,?,?)",
                    (slug, name, "Active" if slug == "real-life-iq" else "Incubator", now, now),
                )
    con.commit()


def install_published_dashboard(app, templates, ctx, db_connect) -> None:
    @app.get("/production/{channel_slug}", response_class=HTMLResponse, name="production_channel")
    def production_channel(request: Request, channel_slug: str):
        con = db_connect()
        try:
            ensure_published_catalog(con)
            channel = None
            if SEED_PATH.exists():
                payload = json.loads(SEED_PATH.read_text(encoding="utf-8"))
                channel = next((c for c in payload.get("channels", []) if c.get("slug") == channel_slug), None)
            if channel is None:
                raise HTTPException(404)

            rows = con.execute(
                """SELECT * FROM published_catalog
                   WHERE channel_slug=?
                   ORDER BY sequence_no DESC""",
                (channel_slug,),
            ).fetchall()
            latest_date = rows[0]["publish_date"] if rows else None
            return templates.TemplateResponse(
                request,
                "published_channel.html",
                ctx(
                    request,
                    selected_channel=channel,
                    published_videos=rows,
                    latest_date=latest_date,
                ),
            )
        finally:
            con.close()
