from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


PRODUCTION_PIPELINE = [
    ("problem", "Problem Statement"),
    ("trigger", "Trigger"),
    ("slides", "Slides"),
    ("script", "Script"),
    ("voice", "Voice-over"),
    ("video", "Video"),
]

PUBLISHED_IDEA_IDS = {
    "P001",  # Bank scam
    "P002",  # Fake toll text
    "P003",  # Package delivery text scam
    "P004",  # WhatsApp verification code
    "P005",  # Gas-station theft
    "P006",  # ATM skimmer
    "P007",  # Package delivered / porch theft
    "P008",  # AI voice-cloning emergency call
    "P009",  # Fake job / task scam
    "P013",  # WhatsApp investment group
    "P061",  # Phone stolen / recovery series
    "P062",  # Gmail recovery
    "P063",  # Bank account recovery
    "P064",  # Instagram recovery
    "P065",  # SIM swap recovery
    "P066",  # Sent money to scammer
    "P068",  # Facebook hacked recovery
    "P071",  # Lost/stolen card recovery
    "P088",  # AirPods recovery
    "P090",  # Lost luggage recovery
}


def _ensure_video_schema(con):
    columns = {row["name"] for row in con.execute("PRAGMA table_info(videos)").fetchall()}
    additions = {
        "youtube_tags": "TEXT",
        "voice_over_text": "TEXT",
        "trigger_text": "TEXT",
        "script_text": "TEXT",
        "channel_id": "INTEGER",
        "channel_video_no": "INTEGER",
    }
    for name, sql_type in additions.items():
        if name not in columns:
            con.execute(f"ALTER TABLE videos ADD COLUMN {name} {sql_type}")


def _apply_six_phase_pipeline(con, ensure_stages):
    # Keep the live app's future-video pipeline aligned with the owner's locked workflow.
    pipeline = ensure_stages.__globals__.get("PIPELINE")
    if isinstance(pipeline, list):
        pipeline[:] = PRODUCTION_PIPELINE

    valid_keys = {key for key, _ in PRODUCTION_PIPELINE}
    placeholders = ",".join("?" for _ in valid_keys)
    con.execute(
        f"DELETE FROM stages WHERE stage_key NOT IN ({placeholders})",
        tuple(valid_keys),
    )

    video_ids = [row["id"] for row in con.execute("SELECT id FROM videos").fetchall()]
    for video_id in video_ids:
        for order_no, (key, name) in enumerate(PRODUCTION_PIPELINE, start=1):
            con.execute(
                """INSERT OR IGNORE INTO stages
                   (video_id,stage_key,stage_name,order_no,status,approved_at)
                   VALUES(?,?,?,?,?,NULL)""",
                (video_id, key, name, order_no, "Not Started"),
            )
            con.execute(
                "UPDATE stages SET stage_name=?, order_no=? WHERE video_id=? AND stage_key=?",
                (name, order_no, video_id, key),
            )


def _load_channel_snapshot():
    path = Path(__file__).resolve().parent / "seed" / "published_videos.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _find_published_workspace(con, channel_no: int, title: str):
    """Find the correct production workspace without assuming workspace # == YouTube #.

    Early REAL-LIFE IQ videos used matching production and publication numbers. Later
    projects developed gaps, so published order must live in channel_video_no instead
    of overwriting the video's global production number.
    """
    video = con.execute(
        "SELECT * FROM videos WHERE channel_id=1 AND channel_video_no=?",
        (channel_no,),
    ).fetchone()
    if video:
        return video

    video = con.execute("SELECT * FROM videos WHERE title=?", (title,)).fetchone()
    if video:
        return video

    # Legacy fallback is safe only for the original contiguous first 25 publications.
    if channel_no <= 25:
        return con.execute("SELECT * FROM videos WHERE number=?", (channel_no,)).fetchone()
    return None


def _next_safe_workspace_number(con, preferred: int) -> int:
    if not con.execute("SELECT 1 FROM videos WHERE number=?", (preferred,)).fetchone():
        return preferred
    return int(con.execute("SELECT COALESCE(MAX(number),0)+1 n FROM videos").fetchone()["n"])


def sync_whatsapp_series(db_connect, ensure_stages):
    """Synchronize REAL-LIFE IQ's published channel library and production workflow."""
    con = db_connect()
    now = datetime.now().isoformat(timespec="seconds")

    _ensure_video_schema(con)
    _apply_six_phase_pipeline(con, ensure_stages)

    snapshot = _load_channel_snapshot()
    if snapshot:
        captured_at = snapshot.get("captured_at") or datetime.now().date().isoformat()

        for row in snapshot.get("videos", []):
            channel_no = int(row["number"])
            topic = row["topic"]
            title = row["title"]
            publish_date = row["publish_date"]

            video = _find_published_workspace(con, channel_no, title)
            if not video:
                workspace_no = _next_safe_workspace_number(con, channel_no)
                cur = con.execute(
                    """INSERT INTO videos
                       (number,topic,title,status,upload_date,publish_date,created_at,updated_at,channel_id,channel_video_no)
                       VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (workspace_no, topic, title, "Published", publish_date, publish_date, now, now, 1, channel_no),
                )
                video_id = cur.lastrowid
                ensure_stages(con, video_id)
            else:
                video_id = video["id"]
                con.execute(
                    """UPDATE videos
                       SET topic=?, title=?, status='Published',
                           upload_date=?, publish_date=?, updated_at=?,
                           channel_id=1, channel_video_no=?
                       WHERE id=?""",
                    (topic, title, publish_date, publish_date, now, channel_no, video_id),
                )

            # Published videos have completed all six production phases.
            for order_no, (key, name) in enumerate(PRODUCTION_PIPELINE, start=1):
                con.execute(
                    """INSERT OR IGNORE INTO stages
                       (video_id,stage_key,stage_name,order_no,status,approved_at)
                       VALUES(?,?,?,?,?,?)""",
                    (video_id, key, name, order_no, "Approved", now),
                )
                con.execute(
                    """UPDATE stages
                       SET stage_name=?, order_no=?, status='Approved',
                           approved_at=COALESCE(approved_at, ?)
                       WHERE video_id=? AND stage_key=?""",
                    (name, order_no, now, video_id, key),
                )

            # Idempotent snapshot metric from the owner's YouTube Studio capture.
            exists = con.execute(
                "SELECT 1 FROM metrics WHERE video_id=? AND captured_at=? LIMIT 1",
                (video_id, captured_at),
            ).fetchone()
            if not exists:
                con.execute(
                    """INSERT INTO metrics
                       (video_id,captured_at,views,likes,comments,subscribers,notes)
                       VALUES(?,?,?,?,?,?,?)""",
                    (
                        video_id,
                        captured_at,
                        int(row.get("views") or 0),
                        0,
                        int(row.get("comments") or 0),
                        0,
                        "YouTube Studio snapshot supplied by channel owner.",
                    ),
                )

    # Keep completed ideas from reappearing as future priorities.
    tables = {row["name"] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    if "ideas" in tables:
        for idea_id in PUBLISHED_IDEA_IDS:
            con.execute("UPDATE ideas SET status='Published' WHERE idea_id=?", (idea_id,))

    con.commit()
    con.close()
