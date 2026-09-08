from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data"))).resolve()
DB_PATH = DATA_DIR / "studio.db"
_DONE = False

PIPELINE = [
    ("problem", "Problem Definition"),
    ("slides", "Slides Verification"),
    ("voice", "Voice-over Verification"),
    ("publishing", "Publishing Plan"),
    ("final_video", "Final Video"),
    ("published", "Published"),
    ("metrics", "Metrics"),
]

PUBLISH_DATES = {
    1: "2026-09-06",
    2: "2026-09-06",
    3: "2026-09-07",
    4: "2026-09-07",
    5: "2026-09-08",
    6: "2026-09-08",
    7: "2026-09-08",
    8: "2026-09-08",
}


def sync_confirmed_publications() -> None:
    """Reconcile the eight REAL-LIFE IQ Shorts the user has confirmed as published."""
    global _DONE
    if _DONE or not DB_PATH.exists():
        return

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "videos" not in tables or "stages" not in tables:
            return

        now = datetime.now().isoformat(timespec="seconds")

        # #8 may not exist in older ephemeral databases. Preserve any richer existing
        # record, but create the production slot when it is absent.
        v8 = con.execute("SELECT id FROM videos WHERE number=8").fetchone()
        if not v8:
            cur = con.execute(
                "INSERT INTO videos(number,topic,status,upload_date,publish_date,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                (8, "ATM Skimmer Warning", "Published", PUBLISH_DATES[8], PUBLISH_DATES[8], now, now),
            )
            v8_id = cur.lastrowid
            for order_no, (stage_key, stage_name) in enumerate(PIPELINE, start=1):
                status = "In Review" if stage_key == "metrics" else "Approved"
                approved_at = None if stage_key == "metrics" else now
                con.execute(
                    "INSERT OR IGNORE INTO stages(video_id,stage_key,stage_name,order_no,status,approved_at) VALUES(?,?,?,?,?,?)",
                    (v8_id, stage_key, stage_name, order_no, status, approved_at),
                )

        video_columns = {row["name"] for row in con.execute("PRAGMA table_info(videos)").fetchall()}

        for number, published_date in PUBLISH_DATES.items():
            video = con.execute("SELECT id FROM videos WHERE number=?", (number,)).fetchone()
            if not video:
                continue
            video_id = video["id"]
            con.execute(
                """UPDATE videos
                   SET status='Published',
                       upload_date=COALESCE(upload_date, ?),
                       publish_date=COALESCE(publish_date, ?),
                       updated_at=?
                   WHERE id=?""",
                (published_date, published_date, now, video_id),
            )
            if "channel_id" in video_columns:
                con.execute("UPDATE videos SET channel_id=COALESCE(channel_id,1) WHERE id=?", (video_id,))
            if "channel_video_no" in video_columns:
                con.execute("UPDATE videos SET channel_video_no=COALESCE(channel_video_no,?) WHERE id=?", (number, video_id))

            for order_no, (stage_key, stage_name) in enumerate(PIPELINE, start=1):
                status = "In Review" if stage_key == "metrics" else "Approved"
                approved_at = None if stage_key == "metrics" else now
                con.execute(
                    """INSERT INTO stages(video_id,stage_key,stage_name,order_no,status,approved_at)
                       VALUES(?,?,?,?,?,?)
                       ON CONFLICT(video_id,stage_key) DO UPDATE SET
                         stage_name=excluded.stage_name,
                         order_no=excluded.order_no,
                         status=excluded.status,
                         approved_at=CASE WHEN excluded.status='Approved' THEN COALESCE(stages.approved_at,excluded.approved_at) ELSE NULL END""",
                    (video_id, stage_key, stage_name, order_no, status, approved_at),
                )

        con.commit()
        _DONE = True
    finally:
        con.close()
