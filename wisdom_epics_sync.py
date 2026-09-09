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

CHANNEL_NAME = "Wisdom of Epics"
CHANNEL_TAGLINE = "Ancient epic. Modern strength. Timeless wisdom."

V1_TITLE = "Arjuna Froze Before Battle — What Krishna Taught Him #Shorts"
V1_VOICE = """On the battlefield of Kurukshetra, Arjuna asked Krishna to place the chariot between the two armies. Then he saw teachers, relatives, and loved ones on both sides. His body trembled, his mouth went dry, and his bow, Gandiva, slipped from his hand. Overcome by grief and confusion, he said he could not see what was right and asked Krishna to guide him. Krishna taught him to act according to duty, with a steady mind, without being attached to the result. The lesson is not to ignore fear. It is to seek clarity, do what is right, and act with purpose. Mahabharata — Timeless Wisdom."""

V2_TOPIC = "Karna: Loyalty at a Terrible Price"
V2_TITLE = "Karna Chose Loyalty — Even When It Cost Him Everything #Shorts"
V2_PROBLEM = "Loyalty is often treated as an unquestioned virtue, but loyalty can become destructive when it keeps us tied to harmful choices or people whose actions conflict with our values."
V2_TAKEAWAY = "Loyalty matters, but it needs moral boundaries. Be grateful to people who stood by you, while still asking whether the path you are supporting is right."
V2_HASHTAGS = "#Mahabharata #Karna #Duryodhana #Kunti #IndianEpic #LifeLessons #Loyalty #Wisdom #Dharma #EmotionalIntelligence #AnimatedStories #Shorts"
V2_TAGS = "Mahabharata, Karna, Duryodhana, Kunti, Karna story, Mahabharata story, animated Mahabharata, loyalty, gratitude, dharma, moral courage, life lessons, Indian epic, timeless wisdom, Wisdom of Epics"
V2_DESCRIPTION = """Karna's loyalty to Duryodhana is one of the Mahabharata's most powerful and tragic relationships.

When Karna was publicly challenged over his status, Duryodhana made him king of Anga and asked for his friendship. Years later, just before the Kurukshetra war, Kunti revealed that Karna was her firstborn son and asked him to join the Pandavas.

Karna chose not to abandon Duryodhana. His decision shows both the strength of gratitude and the danger of loyalty without moral boundaries.

Wisdom of Epics
Ancient epic. Modern strength. Timeless wisdom."""
V2_NOTES = """WISDOM OF EPICS — VIDEO #2 — PRIORITY A+.

Source concept: MHB-002 — Karna: Loyalty at a Terrible Price
Theme: loyalty, gratitude, identity, moral boundaries and consequences.

SOURCE-VALIDATED STORY FLOW:
1. Tournament — Karna is challenged over his lineage/status when he seeks to face Arjuna.
2. Duryodhana immediately installs Karna as king of Anga and asks only for his friendship; Karna accepts.
3. Years later, before Kurukshetra, Kunti reveals that Karna is her firstborn son and asks him to join the Pandavas.
4. Karna refuses to abandon Duryodhana, whose friendship and support had defined his place in the world.
5. Karna promises Kunti that he will not kill Yudhishthira, Bhima, Nakula or Sahadeva; his decisive battle will be with Arjuna.
6. Modern takeaway — loyalty is powerful, but loyalty without moral boundaries can bind us to destructive choices.

VISUAL DIRECTION:
- Indian-origin facial features and original character designs.
- Karna should have a distinct recurring visual identity: sun-linked gold/bronze palette, strong but thoughtful expression, warrior-prince styling.
- Duryodhana should look regal, confident and commanding, not cartoonishly evil.
- Kunti should look dignified, mature and emotionally burdened.
- Respectful cinematic Indian-epic aesthetic; no copying TV/film adaptations.
- Vertical 9:16 scenes for Shorts.
- No invented direct quotations; narration should paraphrase the source.

SOURCE ANCHORS:
- Mahabharata, Adi Parva, Section CXXXVIII: Duryodhana installs Karna as king of Anga and asks for his friendship.
- Mahabharata, Udyoga Parva, Sections CXLIV–CXLVI: Kunti reveals Karna's birth, asks him to unite with the Pandavas; Karna declines and pledges safety to four brothers while reserving combat with Arjuna.

Current gate: Slides Verification / storyboard build.
"""


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


def sync_wisdom_epics() -> None:
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
        video_cols = _columns(con, "videos")
        idea_cols = _columns(con, "ideas")
        if "channel_id" not in video_cols:
            con.execute("ALTER TABLE videos ADD COLUMN channel_id INTEGER")
        if "channel_video_no" not in video_cols:
            con.execute("ALTER TABLE videos ADD COLUMN channel_video_no INTEGER")
        if "channel_id" not in idea_cols:
            con.execute("ALTER TABLE ideas ADD COLUMN channel_id INTEGER")

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
        channel = con.execute("SELECT id FROM channels WHERE id=2").fetchone()
        if not channel:
            con.execute(
                """INSERT INTO channels(id,slug,name,status,mission,tagline,audience,content_pillars,format_strategy,
                   language_strategy,visual_style,source_policy,notes,created_at,updated_at)
                   VALUES(2,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    "wisdom-of-epics", CHANNEL_NAME, "Active",
                    "Tell powerful stories from the world's great epics and turn them into practical lessons in character, judgment, courage, resilience, emotional intelligence and wisdom.",
                    CHANNEL_TAGLINE,
                    "A global audience interested in epic stories, personal growth, history, mythology, leadership and timeless life lessons.",
                    "Mahabharata; Ramayana; Bhagavad Gita teachings; Indian epic wisdom; Greek and Roman epics; Chinese and Japanese classics; courage; leadership; loyalty; duty; resilience; ethics.",
                    "Animated character-driven Shorts for discovery, with selected longer episodes for deeper storytelling.",
                    "English originals with automatic dubbing; expand creator-produced languages based on performance.",
                    "Original cinematic character designs, culturally respectful settings, emotional storytelling, strong continuity and clean 9:16 composition.",
                    "Use reputable primary texts and scholarship. Paraphrase rather than copy modern copyrighted translations; acknowledge interpretive variation and never copy TV/film dialogue, music or character designs.",
                    "Channel renamed by creator from Mahabharata — Timeless Wisdom to Wisdom of Epics after publication of Video #1.",
                    now, now,
                ),
            )
        else:
            con.execute(
                """UPDATE channels SET slug=?,name=?,status='Active',mission=?,tagline=?,audience=?,content_pillars=?,
                   format_strategy=?,language_strategy=?,visual_style=?,source_policy=?,notes=?,updated_at=? WHERE id=2""",
                (
                    "wisdom-of-epics", CHANNEL_NAME,
                    "Tell powerful stories from the world's great epics and turn them into practical lessons in character, judgment, courage, resilience, emotional intelligence and wisdom.",
                    CHANNEL_TAGLINE,
                    "A global audience interested in epic stories, personal growth, history, mythology, leadership and timeless life lessons.",
                    "Mahabharata; Ramayana; Bhagavad Gita teachings; Indian epic wisdom; Greek and Roman epics; Chinese and Japanese classics; courage; leadership; loyalty; duty; resilience; ethics.",
                    "Animated character-driven Shorts for discovery, with selected longer episodes for deeper storytelling.",
                    "English originals with automatic dubbing; expand creator-produced languages based on performance.",
                    "Original cinematic character designs, culturally respectful settings, emotional storytelling, strong continuity and clean 9:16 composition.",
                    "Use reputable primary texts and scholarship. Paraphrase rather than copy modern copyrighted translations; acknowledge interpretive variation and never copy TV/film dialogue, music or character designs.",
                    "Channel renamed by creator from Mahabharata — Timeless Wisdom to Wisdom of Epics after publication of Video #1.",
                    now,
                ),
            )

        # Video #1 is confirmed published by the creator on 2026-09-09.
        v1 = con.execute("SELECT * FROM videos WHERE channel_id=2 AND channel_video_no=1 ORDER BY id LIMIT 1").fetchone()
        if v1:
            v1_id = v1["id"]
            con.execute("UPDATE videos SET title=?,status='Published',updated_at=? WHERE id=?", (V1_TITLE, now, v1_id))
            _set_optional(con, v1_id, {
                "voice_over_text": V1_VOICE,
                "published_at": "2026-09-09T00:00:00",
                "notes": "Published as Wisdom of Epics Video #1 on 2026-09-09. Final local video passed visual correction for duplicate caption overlay before upload.",
            })
            for order_no, (key, name) in enumerate(PIPELINE, start=1):
                _set_stage(con, v1_id, key, name, order_no, "In Review" if key == "metrics" else "Approved", now)

        con.execute(
            """UPDATE ideas SET channel_id=2,status='Published',priority='Published #1',score=10.0,
               notes=? WHERE idea_id='MHB-001'""",
            ("Published as Wisdom of Epics Video #1 on 2026-09-09.",),
        )

        # Prioritize MHB-002.
        idea2 = con.execute("SELECT id FROM ideas WHERE idea_id='MHB-002'").fetchone()
        if idea2:
            con.execute(
                """UPDATE ideas SET channel_id=2,pillar='Loyalty & Moral Boundaries',series='Wisdom of Epics — Mahabharata',
                   working_title=?,hook=?,problem=?,safe_action=?,audience=?,priority='A+ / VIDEO #2',score=9.9,status='In Production',
                   source_name=?,notes=? WHERE idea_id='MHB-002'""",
                (
                    V2_TOPIC,
                    "What happens when loyalty to the person who believed in you pulls you toward a path you know may end in tragedy?",
                    V2_PROBLEM, V2_TAKEAWAY, "Global personal-growth and epic-story audience",
                    "Mahabharata — Adi Parva CXXXVIII; Udyoga Parva CXLIV–CXLVI",
                    "Selected as Wisdom of Epics Video #2. Current gate: storyboard/slides verification.",
                ),
            )
        else:
            con.execute(
                """INSERT INTO ideas(idea_id,pillar,series,working_title,hook,problem,safe_action,audience,priority,score,status,
                   source_name,source_url,notes,created_at,channel_id)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    "MHB-002", "Loyalty & Moral Boundaries", "Wisdom of Epics — Mahabharata", V2_TOPIC,
                    "What happens when loyalty to the person who believed in you pulls you toward a path you know may end in tragedy?",
                    V2_PROBLEM, V2_TAKEAWAY, "Global personal-growth and epic-story audience",
                    "A+ / VIDEO #2", 9.9, "In Production",
                    "Mahabharata — Adi Parva CXXXVIII; Udyoga Parva CXLIV–CXLVI", None,
                    "Selected as Wisdom of Epics Video #2. Current gate: storyboard/slides verification.", now, 2,
                ),
            )

        v2 = con.execute("SELECT * FROM videos WHERE channel_id=2 AND channel_video_no=2 ORDER BY id LIMIT 1").fetchone()
        if not v2:
            internal_no = 1002
            while con.execute("SELECT 1 FROM videos WHERE number=?", (internal_no,)).fetchone():
                internal_no += 1
            cur = con.execute(
                """INSERT INTO videos(number,channel_id,channel_video_no,topic,title,description,hashtags,status,problem,takeaway,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (internal_no, 2, 2, V2_TOPIC, V2_TITLE, V2_DESCRIPTION, V2_HASHTAGS, "Slides Verification", V2_PROBLEM, V2_TAKEAWAY, now, now),
            )
            v2_id = cur.lastrowid
        else:
            v2_id = v2["id"]
            con.execute(
                """UPDATE videos SET topic=?,title=?,description=?,hashtags=?,status='Slides Verification',problem=?,takeaway=?,updated_at=? WHERE id=?""",
                (V2_TOPIC, V2_TITLE, V2_DESCRIPTION, V2_HASHTAGS, V2_PROBLEM, V2_TAKEAWAY, now, v2_id),
            )

        _set_optional(con, v2_id, {"youtube_tags": V2_TAGS, "notes": V2_NOTES})
        for order_no, (key, name) in enumerate(PIPELINE, start=1):
            if key == "problem":
                status = "Approved"
            elif key == "slides":
                status = "In Review"
            else:
                status = "Not Started"
            _set_stage(con, v2_id, key, name, order_no, status, now)

        con.commit()
        _DONE = True
    finally:
        con.close()
