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

V2_TITLE = "Karna Chose Loyalty — Even When It Cost Him Everything #Shorts"
V2_TOPIC = "Karna: Loyalty at a Terrible Price"
V2_DESCRIPTION = """Karna’s loyalty to Duryodhana is one of the Mahabharata’s most powerful and tragic relationships.

At a royal tournament in Hastinapura, Karna’s birth and status were questioned. Duryodhana stood beside him, crowned him King of Anga, and offered him friendship.

Years later, Kunti revealed that Karna was her firstborn son and asked him to join the Pandavas. Karna still chose not to abandon Duryodhana, the friend who had supported him when others rejected him.

He promised Kunti that he would spare Yudhishthira, Bhima, Nakula, and Sahadeva, leaving his final contest for Arjuna.

The lesson: loyalty can be noble, but loyalty without moral boundaries can lead to painful choices.

Wisdom of Epics
Ancient epic. Modern strength. Timeless wisdom."""
V2_HASHTAGS = "#Mahabharata #Karna #Duryodhana #Kunti #Arjuna #IndianEpic #Loyalty #Dharma #LifeLessons #Wisdom #AnimatedStories #Shorts"
V2_TAGS = "Mahabharata, Karna, Duryodhana, Kunti, Arjuna, Karna story, Karna and Duryodhana, Mahabharata story, animated Mahabharata, Indian epic, Indian mythology, loyalty, dharma, gratitude, moral choices, life lessons, timeless wisdom, Wisdom of Epics"
V2_VOICE = """At a royal tournament in Hastinapura, Karna challenged Arjuna. When his birth and status were questioned, Duryodhana stood beside him, crowned him king of Anga, and offered him friendship.

Years later, before the war, Kunti revealed that Karna was her firstborn son and asked him to join the Pandavas.

Karna refused to abandon Duryodhana, the friend who had supported him when others rejected him. But he promised Kunti he would spare Yudhishthira, Bhima, Nakula, and Sahadeva, leaving his final contest for Arjuna.

Karna’s story reminds us: loyalty can be noble, but loyalty without moral boundaries can lead to painful choices.

Wisdom of Epics."""
V2_PROBLEM = "Loyalty can become destructive when gratitude or obligation keeps us tied to choices that conflict with our values."
V2_TAKEAWAY = "Loyalty matters, but it needs moral boundaries. Gratitude should not replace ethical judgment."
V2_PINNED = "Was Karna right to remain loyal to Duryodhana after learning the truth about his birth? Loyalty can be powerful—but where should we draw the line?"
V2_NOTES = """Published as Wisdom of Epics Video #2 on 2026-09-09.
Final creator-approved render: 1080x1920, true 9:16 vertical, no overlapping/background slide bleed.
Narration: NexusTTS, English (India), Aarav — Old Time Storyteller, 1.0x.
YouTube AI use disclosure: Yes, because the video contains realistic-looking AI-generated mythological scenes that did not occur as filmed footage.
Current gate: Metrics / post-publication performance review."""


def _columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}


def _set_optional(con: sqlite3.Connection, video_id: int, values: dict[str, object]) -> None:
    cols = _columns(con, "videos")
    usable = {k: v for k, v in values.items() if k in cols}
    if not usable:
        return
    sql = ", ".join(f"{k}=?" for k in usable)
    con.execute(f"UPDATE videos SET {sql} WHERE id=?", (*usable.values(), video_id))


def _set_stage(con: sqlite3.Connection, video_id: int, stage_key: str, stage_name: str, order_no: int, status: str, now: str) -> None:
    approved_at = now if status == "Approved" else None
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


def sync_wisdom_epics_publications() -> None:
    global _DONE
    if _DONE or not DB_PATH.exists():
        return

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if not {"videos", "stages", "ideas"}.issubset(tables):
            return

        now = datetime.now().isoformat(timespec="seconds")
        v2 = con.execute(
            "SELECT * FROM videos WHERE channel_id=2 AND channel_video_no=2 ORDER BY id LIMIT 1"
        ).fetchone()
        if not v2:
            return

        v2_id = v2["id"]
        con.execute(
            """UPDATE videos
               SET topic=?,title=?,description=?,hashtags=?,status='Published',problem=?,takeaway=?,updated_at=?
               WHERE id=?""",
            (V2_TOPIC, V2_TITLE, V2_DESCRIPTION, V2_HASHTAGS, V2_PROBLEM, V2_TAKEAWAY, now, v2_id),
        )
        _set_optional(
            con,
            v2_id,
            {
                "upload_date": "2026-09-09",
                "publish_date": "2026-09-09",
                "published_at": "2026-09-09T00:00:00",
                "voice_over_text": V2_VOICE,
                "youtube_tags": V2_TAGS,
                "pinned_comment": V2_PINNED,
                "notes": V2_NOTES,
            },
        )

        for order_no, (key, name) in enumerate(PIPELINE, start=1):
            _set_stage(con, v2_id, key, name, order_no, "In Review" if key == "metrics" else "Approved", now)

        con.execute(
            """UPDATE ideas
               SET channel_id=2,status='Published',priority='Published #2',score=10.0,
                   notes=?
               WHERE idea_id='MHB-002'""",
            ("Published as Wisdom of Epics Video #2 on 2026-09-09. Current gate: Metrics.",),
        )

        con.commit()
        _DONE = True
    finally:
        con.close()
