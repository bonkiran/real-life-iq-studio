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

V3_TITLE = "Draupadi Asked One Question — And the Court Fell Silent #Shorts"
V3_TOPIC = "Draupadi in the Royal Court"
V3_DESCRIPTION = """After the dice game, Draupadi was brought before the Kuru court and asked a devastating question: if Yudhishthira had already lost himself, did he still have the right to stake her?

Surrounded by kings, teachers, and elders, she demanded an answer while many remained silent. In the traditional telling, when Dushasana attempted to dishonor her, Draupadi turned to Krishna in prayer—and her sari would not end.

Her story carries a timeless lesson: when people with power stay silent before injustice, silence can become part of the injustice.

Wisdom of Epics
Ancient epic. Modern strength. Timeless wisdom.

Based on the Mahabharata, Sabha Parva. Some details of the Draupadi disrobing episode vary across textual traditions and retellings."""
V3_HASHTAGS = "#Draupadi #Mahabharata #Krishna #Dharma #IndianEpics #LifeLessons #MoralCourage #Wisdom #Mythology #WisdomOfEpics #Shorts"
V3_TAGS = "Draupadi, Mahabharata, Draupadi story, Draupadi court scene, Draupadi vastraharan, Krishna Draupadi, Mahabharata stories, Indian mythology, Indian epics, dharma, moral courage, injustice, silence and injustice, life lessons, ancient wisdom, epic stories, Wisdom of Epics"
V3_VOICE = """After the dice game, Draupadi was summoned to the Kuru court.

She asked one devastating question: if Yudhishthira had already lost himself, did he still have the right to stake her?

The hall was filled with kings, teachers, and elders—yet most stayed silent. Bhishma called the question of dharma difficult. Vikarna and Vidura protested, but the humiliation continued.

In the traditional telling, when Dushasana tried to pull away her sari, Draupadi prayed—and the cloth would not end.

Her dignity survived what the court failed to stop.

The lesson: when people with power stay silent before injustice, silence can become part of the injustice.

Wisdom of Epics."""
V3_PROBLEM = "Draupadi confronts humiliation and injustice while many respected and powerful people in the royal court remain silent."
V3_TAKEAWAY = "When people with power stay silent before injustice, silence can become part of the injustice. Dignity includes questioning normalized wrongdoing."
V3_PINNED = """Draupadi’s question is what makes this story so powerful: when something is clearly wrong, is staying silent really neutral?

What do you think — who had the greatest responsibility to speak up in that court?

Wisdom of Epics — Ancient epic. Modern strength. Timeless wisdom."""
V3_NOTES = """Published as Wisdom of Epics Video #3 on 2026-09-09.
Source concept: MHB-003 — Draupadi in the Royal Court.
Final creator-approved render: Wisdom_of_Epics_03_Draupadi_Royal_Court_FINAL.mp4.
Validated master: 1080x1920, true 9:16, 30 fps, H.264 video, AAC audio, duration 39.549 seconds, fast-start enabled.
Visual format: premium illustrated storytelling with mythical gold-on-maroon caption panels, clean hard cuts, no blurred backing or neighboring-slide bleed.
Voice-over: creator-supplied Indian voice MP3, technically validated with no clipping detected.
YouTube AI/synthetic-content disclosure: Yes.
Pinned comment saved with the publication package.
Textual caution retained: the narration says 'In the traditional telling' for the endless-sari sequence because details vary across textual traditions and retellings.
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


def _publish_video(
    con: sqlite3.Connection,
    *,
    channel_video_no: int,
    topic: str,
    title: str,
    description: str,
    hashtags: str,
    problem: str,
    takeaway: str,
    voice: str,
    tags: str,
    pinned: str,
    notes: str,
    idea_id: str,
    published_priority: str,
    now: str,
) -> None:
    video = con.execute(
        "SELECT * FROM videos WHERE channel_id=2 AND channel_video_no=? ORDER BY id LIMIT 1",
        (channel_video_no,),
    ).fetchone()

    if not video:
        internal_no = 1000 + channel_video_no
        while con.execute("SELECT 1 FROM videos WHERE number=?", (internal_no,)).fetchone():
            internal_no += 1000
        cur = con.execute(
            """INSERT INTO videos(number,channel_id,channel_video_no,topic,title,description,hashtags,status,problem,takeaway,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (internal_no, 2, channel_video_no, topic, title, description, hashtags, "Published", problem, takeaway, now, now),
        )
        video_id = cur.lastrowid
    else:
        video_id = video["id"]
        con.execute(
            """UPDATE videos
               SET topic=?,title=?,description=?,hashtags=?,status='Published',problem=?,takeaway=?,updated_at=?
               WHERE id=?""",
            (topic, title, description, hashtags, problem, takeaway, now, video_id),
        )

    _set_optional(
        con,
        video_id,
        {
            "upload_date": "2026-09-09",
            "publish_date": "2026-09-09",
            "published_at": "2026-09-09T00:00:00",
            "voice_over_text": voice,
            "youtube_tags": tags,
            "pinned_comment": pinned,
            "notes": notes,
        },
    )

    for order_no, (key, name) in enumerate(PIPELINE, start=1):
        _set_stage(con, video_id, key, name, order_no, "In Review" if key == "metrics" else "Approved", now)

    con.execute(
        """UPDATE ideas
           SET channel_id=2,status='Published',priority=?,score=10.0,notes=?
           WHERE idea_id=?""",
        (published_priority, f"Published as Wisdom of Epics Video #{channel_video_no} on 2026-09-09. Current gate: Metrics.", idea_id),
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

        _publish_video(
            con,
            channel_video_no=2,
            topic=V2_TOPIC,
            title=V2_TITLE,
            description=V2_DESCRIPTION,
            hashtags=V2_HASHTAGS,
            problem=V2_PROBLEM,
            takeaway=V2_TAKEAWAY,
            voice=V2_VOICE,
            tags=V2_TAGS,
            pinned=V2_PINNED,
            notes=V2_NOTES,
            idea_id="MHB-002",
            published_priority="Published #2",
            now=now,
        )

        _publish_video(
            con,
            channel_video_no=3,
            topic=V3_TOPIC,
            title=V3_TITLE,
            description=V3_DESCRIPTION,
            hashtags=V3_HASHTAGS,
            problem=V3_PROBLEM,
            takeaway=V3_TAKEAWAY,
            voice=V3_VOICE,
            tags=V3_TAGS,
            pinned=V3_PINNED,
            notes=V3_NOTES,
            idea_id="MHB-003",
            published_priority="Published #3",
            now=now,
        )

        con.commit()
        _DONE = True
    finally:
        con.close()
