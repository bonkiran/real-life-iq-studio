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

TITLE = "Arjuna Froze Before Battle — What Krishna Taught Him #Shorts"
DESCRIPTION = """What happens when even the bravest warrior loses confidence?

Before the great battle of Kurukshetra, Arjuna becomes overwhelmed with fear, emotion, and doubt. In that moment, Krishna begins guiding him toward clarity, duty, and right action.

This timeless Mahabharata story reminds us that feeling afraid does not make us weak. What matters is how we move from confusion toward clear, purposeful action.

Mahabharata — Timeless Wisdom
Ancient epic. Modern strength. Timeless wisdom."""
HASHTAGS = "#Mahabharata #Arjuna #Krishna #BhagavadGita #IndianEpic #AnimatedStories #LifeLessons #Wisdom #EmotionalIntelligence #Confidence #Courage #Shorts"
TAGS = "Mahabharata, Arjuna, Krishna, Bhagavad Gita, Kurukshetra, Mahabharata story, animated Mahabharata, life lessons, courage, confidence, emotional intelligence, Indian epic, timeless wisdom, animated stories"
PROBLEM = "People can lose confidence, freeze, or become emotionally overwhelmed before an important task or difficult decision. Arjuna's crisis before Kurukshetra provides a powerful story framework for showing that even a highly capable person can experience fear and confusion."
TAKEAWAY = "Fear and doubt can happen even to strong people. Pause, seek clarity, separate emotion from responsibility, and act according to your values and purpose rather than panic."
DRAFT_VOICE = """On the battlefield of Kurukshetra, Arjuna asked Krishna to place the chariot between the two armies. Then he saw teachers, relatives, and loved ones on both sides. His body trembled, his mouth went dry, and his bow slipped from his hand. Overcome by grief and confusion, he said he could not see what was right and asked Krishna to guide him. Krishna taught him to act according to duty, with a steady mind, without being attached to the result. The lesson is not to ignore fear. It is to seek clarity, do what is right, and act with purpose. Mahabharata — Timeless Wisdom."""
NOTES = f"""OFFICIAL MAHABHARATA LAUNCH VIDEO — PRIORITY #1.

Channel video: #1
Source concept: MHB-001 — Arjuna Freezes Before Kurukshetra
Theme: Courage, confusion, duty, inner strength and purposeful action.

APPROVED VISUAL STORYBOARD — 6 SCENES:
1. Hook — Arjuna stands between the two armies as the battle is about to begin.
2. Emotional conflict — he sees relatives, teachers and loved ones on both sides.
3. Crisis — he becomes physically and emotionally overwhelmed; Gandiva slips from his hand.
4. Krishna begins guiding him after Arjuna acknowledges his confusion and asks for guidance.
5. Lesson — duty, discernment, steady action and freedom from attachment to results.
6. Modern takeaway — do not ignore fear; seek clarity, do what is right and act with purpose.

VISUAL DIRECTION LOCKED:
- Indian-origin facial features and character styling.
- Original character designs only; do not imitate copyrighted TV/film adaptations.
- Respectful, cinematic, emotionally expressive Indian-epic aesthetic.
- Same Arjuna/Krishna appearance, costume palette, chariot and dawn battlefield continuity across scenes.
- Vertical 9:16 composition for Shorts.

SOURCE VALIDATION:
- Bhagavad Gita Chapter 1: Arjuna's grief and physical distress, including Gandiva slipping from his hand.
- Bhagavad Gita 2.7: Arjuna acknowledges confusion about duty and asks Krishna for guidance.
- Bhagavad Gita 2.47 and surrounding teaching: perform duty/right action without attachment to results.
- Do not reduce the Gita to generic confidence advice; preserve moral crisis, discernment, duty and action.

DRAFT VOICE-OVER FOR REVIEW — NOT YET APPROVED:
{DRAFT_VOICE}

Current gate: Voice-over Verification. Slides/animation concept approved by user on 2026-09-08.
"""


def _columns(con, table: str) -> set[str]:
    return {row["name"] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}


def sync_mahabharata_launch() -> None:
    """Persist the selected first Mahabharata video and its launch priority."""
    global _DONE
    if _DONE or not DB_PATH.exists():
        return

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "videos" not in tables or "stages" not in tables or "ideas" not in tables:
            return

        now = datetime.now().isoformat(timespec="seconds")

        video_cols = _columns(con, "videos")
        if "channel_id" not in video_cols:
            con.execute("ALTER TABLE videos ADD COLUMN channel_id INTEGER")
        if "channel_video_no" not in video_cols:
            con.execute("ALTER TABLE videos ADD COLUMN channel_video_no INTEGER")
        idea_cols = _columns(con, "ideas")
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
        con.execute(
            """INSERT OR IGNORE INTO channels(
                 id,slug,name,status,mission,tagline,audience,content_pillars,format_strategy,
                 language_strategy,visual_style,source_policy,notes,created_at,updated_at)
               VALUES(2,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                "mahabharata-timeless-wisdom",
                "Mahabharata — Timeless Wisdom",
                "Incubator",
                "Use important Mahabharata stories to teach timeless lessons in morality, emotional intelligence, character, strength, wisdom, inner belief and core confidence.",
                "Ancient epic. Modern strength. Timeless wisdom.",
                "A global audience interested in powerful stories, personal growth, emotional intelligence, leadership, resilience and Indian epic wisdom.",
                "Courage and self-belief; duty and decision-making; emotional intelligence; leadership; loyalty; ego and jealousy; sacrifice; resilience; wisdom and ethics.",
                "Animated character-driven stories. Shorts for discovery plus longer episodes for deeper storytelling.",
                "English originals with YouTube automatic dubbing; expand creator-produced languages based on performance.",
                "Original cinematic character designs with recurring visual continuity; respectful, emotionally expressive and globally accessible.",
                "Base scripts on reputable Mahabharata textual sources and scholarship. Do not copy dialogue, music, imagery or character designs from copyrighted adaptations; acknowledge interpretive variation.",
                "Core promise: Stories from the Mahabharata that teach you how to think, choose, endure and grow.",
                now,
                now,
            ),
        )

        idea = con.execute("SELECT id FROM ideas WHERE idea_id='MHB-001'").fetchone()
        if not idea:
            con.execute(
                """INSERT INTO ideas(
                     idea_id,pillar,series,working_title,hook,problem,safe_action,audience,priority,score,status,
                     source_name,source_url,notes,created_at,channel_id)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    "MHB-001",
                    "Courage & Self-Belief",
                    "Mahabharata — Timeless Wisdom",
                    "Arjuna Freezes Before Kurukshetra",
                    "What do you do when the biggest challenge of your life makes you doubt everything?",
                    PROBLEM,
                    TAKEAWAY,
                    "Global personal-growth audience",
                    "A+ / LAUNCH #1",
                    10.0,
                    "In Production",
                    "Mahabharata / Bhagavad Gita source validation required",
                    None,
                    "Selected as the official first animated Short. Visual storyboard approved; current gate is voice-over review.",
                    now,
                    2,
                ),
            )
        else:
            con.execute(
                """UPDATE ideas SET channel_id=2, priority='A+ / LAUNCH #1', score=10.0,
                   status='In Production', problem=?, safe_action=?, notes=? WHERE idea_id='MHB-001'""",
                (
                    PROBLEM,
                    TAKEAWAY,
                    "Selected as the official first animated Short. Visual storyboard approved; current gate: Voice-over Verification.",
                ),
            )

        video = con.execute(
            "SELECT * FROM videos WHERE channel_id=2 AND channel_video_no=1 ORDER BY id LIMIT 1"
        ).fetchone()
        if not video:
            internal_no = 1001
            while con.execute("SELECT 1 FROM videos WHERE number=?", (internal_no,)).fetchone():
                internal_no += 1
            cur = con.execute(
                """INSERT INTO videos(
                     number,channel_id,channel_video_no,topic,title,description,hashtags,status,problem,takeaway,
                     created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    internal_no,
                    2,
                    1,
                    "Arjuna Freezes Before Kurukshetra",
                    TITLE,
                    DESCRIPTION,
                    HASHTAGS,
                    "Voice-over Verification",
                    PROBLEM,
                    TAKEAWAY,
                    now,
                    now,
                ),
            )
            video_id = cur.lastrowid
        else:
            video_id = video["id"]
            con.execute(
                """UPDATE videos SET topic=?,title=?,description=?,hashtags=?,status='Voice-over Verification',
                   problem=?,takeaway=?,updated_at=? WHERE id=?""",
                ("Arjuna Freezes Before Kurukshetra", TITLE, DESCRIPTION, HASHTAGS, PROBLEM, TAKEAWAY, now, video_id),
            )

        current_cols = _columns(con, "videos")
        if "youtube_tags" in current_cols:
            con.execute("UPDATE videos SET youtube_tags=? WHERE id=?", (TAGS, video_id))
        if "notes" in current_cols:
            con.execute("UPDATE videos SET notes=? WHERE id=?", (NOTES.strip(), video_id))
        # Keep voice_over_text empty until the user approves the narration.

        for order_no, (stage_key, stage_name) in enumerate(PIPELINE, start=1):
            if stage_key in {"problem", "slides"}:
                status = "Approved"
                approved_at = now
            elif stage_key == "voice":
                status = "In Review"
                approved_at = None
            else:
                status = "Not Started"
                approved_at = None
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
