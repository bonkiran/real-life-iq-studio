from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
import os

from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data"))).resolve()
DB_PATH = DATA_DIR / "studio.db"
templates = Jinja2Templates(directory=BASE_DIR / "templates")

PIPELINE = [
    ("problem", "Problem Definition"),
    ("slides", "Slides Verification"),
    ("voice", "Voice-over Verification"),
    ("publishing", "Publishing Plan"),
    ("final_video", "Final Video"),
    ("published", "Published"),
    ("metrics", "Metrics"),
]


def _db_connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _column_names(con, table: str) -> set[str]:
    return {row["name"] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}


def _ensure_schema(con):
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

    video_cols = _column_names(con, "videos")
    if "channel_id" not in video_cols:
        con.execute("ALTER TABLE videos ADD COLUMN channel_id INTEGER")
    if "channel_video_no" not in video_cols:
        con.execute("ALTER TABLE videos ADD COLUMN channel_video_no INTEGER")

    idea_cols = _column_names(con, "ideas")
    if "channel_id" not in idea_cols:
        con.execute("ALTER TABLE ideas ADD COLUMN channel_id INTEGER")

    con.execute(
        """CREATE TABLE IF NOT EXISTS idea_inbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            thought TEXT,
            suggested_channel_id INTEGER,
            status TEXT NOT NULL DEFAULT 'Inbox',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )"""
    )

    now = datetime.now().isoformat(timespec="seconds")
    con.execute(
        """INSERT OR IGNORE INTO channels(
             id,slug,name,handle,status,mission,tagline,audience,content_pillars,
             format_strategy,language_strategy,visual_style,source_policy,notes,created_at,updated_at)
           VALUES(1,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "real-life-iq",
            "REAL-LIFE IQ",
            "@REAL-LIFEIQ",
            "Active",
            "Help ordinary people make safer, smarter everyday decisions and protect their money, identity, accounts, belongings and family trust.",
            "Smarter Choices for Real Life.",
            "Everyday adults and families who want practical, easy-to-remember safety guidance.",
            "Scam awareness; cyber safety; account security; physical theft prevention; payment safety; myth-busting.",
            "Primarily 9:16 Shorts with realistic mini-stories: confusion → suspicion → verification → action → confidence.",
            "English original with YouTube automatic dubbing enabled; add creator-produced language tracks later where performance justifies it.",
            "Realistic people and environments, clean overlays, strong continuity, calm caution rather than fear.",
            "Evidence-first. Prefer primary sources such as FTC, FBI, USPS/USPIS, law enforcement and official platform documentation.",
            "Existing production channel. Preserve the locked workflow: Problem → Slides → Voice-over → Publishing Plan → Final Video → Published → Metrics.",
            now,
            now,
        ),
    )
    con.execute(
        """INSERT OR IGNORE INTO channels(
             id,slug,name,handle,status,mission,tagline,audience,content_pillars,
             format_strategy,language_strategy,visual_style,source_policy,notes,created_at,updated_at)
           VALUES(2,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "mahabharata-timeless-wisdom",
            "Mahabharata — Timeless Wisdom",
            None,
            "Incubator",
            "Use important Mahabharata stories to teach timeless lessons in morality, emotional intelligence, character, strength, wisdom, inner belief and core confidence.",
            "Ancient epic. Modern strength. Timeless wisdom.",
            "A global audience interested in powerful stories, personal growth, emotional intelligence, leadership, resilience and Indian epic wisdom.",
            "Courage and self-belief; duty and decision-making; emotional intelligence; leadership; loyalty; ego and jealousy; sacrifice; resilience; wisdom and ethics.",
            "Animated character-driven stories. Shorts for discovery plus 5–10 minute episodes for deeper storytelling. Each story ends with one practical modern-life lesson.",
            "Start with English originals and use YouTube multi-language dubbing; expand into Hindi and other high-performing languages after analytics show demand.",
            "Original cinematic character designs with recurring visual continuity. Respectful, emotionally expressive and accessible to a worldwide audience.",
            "Base scripts on reputable Mahabharata textual sources and scholarship. Do not copy dialogue, designs, music or scenes from copyrighted TV/film adaptations. Acknowledge where interpretations vary.",
            "Core promise: Stories from the Mahabharata that teach you how to think, choose, endure and grow.",
            now,
            now,
        ),
    )

    # Existing production records belong to REAL-LIFE IQ unless explicitly assigned elsewhere.
    con.execute("UPDATE videos SET channel_id=1 WHERE channel_id IS NULL")
    con.execute("UPDATE videos SET channel_video_no=number WHERE channel_video_no IS NULL AND channel_id=1")
    con.execute("UPDATE ideas SET channel_id=1 WHERE channel_id IS NULL")

    # Seed the initial Mahabharata story map once so the new channel has a useful backlog before production starts.
    existing = con.execute("SELECT COUNT(*) c FROM ideas WHERE idea_id LIKE 'MHB-%'").fetchone()["c"]
    if existing == 0:
        stories = [
            ("MHB-001", "Arjuna Freezes Before Kurukshetra", "Courage & Self-Belief", "What do you do when the biggest challenge of your life makes you doubt everything?", "Arjuna faces fear, confusion and moral paralysis before battle.", "Clarity begins by separating what you control from what you cannot; act from values and duty rather than panic."),
            ("MHB-002", "Karna: Loyalty at a Terrible Price", "Loyalty & Judgment", "Can loyalty still be noble when it keeps you beside the wrong person?", "Karna's gratitude and loyalty to Duryodhana conflict with what he knows about right and wrong.", "Loyalty needs judgment; gratitude should not require abandoning conscience."),
            ("MHB-003", "Draupadi in the Royal Court", "Dignity & Courage", "What gives someone strength when everyone powerful stays silent?", "Draupadi confronts humiliation, injustice and the silence of respected elders.", "Dignity can survive even when circumstances are unjust; courage includes questioning normalized wrongdoing."),
            ("MHB-004", "Abhimanyu and the Chakravyuha", "Courage & Preparation", "Is courage enough when you know only half the way through a dangerous problem?", "Abhimanyu enters a battle formation knowing how to enter but not how to exit.", "Courage is powerful, but preparation, support and understanding the exit strategy matter too."),
            ("MHB-005", "The Yaksha's Questions to Yudhishthira", "Wisdom & Judgment", "Could calm thinking save the people you love when strength cannot?", "Yudhishthira must answer profound questions under pressure.", "Wisdom is the ability to think clearly when emotion and urgency are highest."),
            ("MHB-006", "Ekalavya's Extraordinary Discipline", "Discipline & Fairness", "How far can self-belief take you when no teacher will accept you?", "Ekalavya develops exceptional skill through independent discipline and devotion.", "Resourcefulness and disciplined practice can overcome exclusion, while the story also invites hard questions about fairness and authority."),
            ("MHB-007", "Bhishma's Terrible Vow", "Commitment & Consequences", "Can a promise be so strong that it controls the rest of your life?", "Bhishma makes an extraordinary vow with consequences across generations.", "Commitment is admirable, but every major promise should be examined for its long-term consequences."),
            ("MHB-008", "Duryodhana's Jealousy", "Jealousy & Ego", "Why can another person's success feel like your own failure?", "Duryodhana allows comparison and resentment toward the Pandavas to shape his decisions.", "Unmanaged comparison can turn insecurity into destructive choices; build identity from your own values and progress."),
            ("MHB-009", "Karna Gives Away His Armor", "Generosity & Boundaries", "Can generosity become dangerous when you give away what protects you?", "Karna gives away his natural armor despite knowing the personal cost.", "Generosity is strongest when paired with discernment and healthy boundaries."),
            ("MHB-010", "Yudhishthira and the Dice Game", "Decision-Making & Self-Control", "Why do intelligent people keep going when they know a decision is becoming destructive?", "Yudhishthira continues gambling as the stakes become catastrophic.", "Intelligence does not replace self-control; recognize escalation and create a stopping rule before emotion takes over."),
            ("MHB-011", "Krishna Chooses Peace Before War", "Leadership & Negotiation", "What does real strength look like before conflict begins?", "Krishna attempts diplomacy before accepting that war may be unavoidable.", "Strong leadership exhausts principled paths to peace without confusing patience with weakness."),
            ("MHB-012", "Arjuna Chooses Krishna, Not the Army", "Priorities & Judgment", "Would you choose thousands of soldiers—or one person whose wisdom you trust?", "Arjuna chooses Krishna's guidance while Duryodhana chooses Krishna's army.", "The right guidance can be more valuable than greater visible resources."),
            ("MHB-013", "Vidura Speaks Truth to Power", "Integrity & Leadership", "Would you still tell the truth if the person who needs to hear it can ignore you?", "Vidura repeatedly advises Dhritarashtra against destructive choices.", "Integrity means giving truthful counsel even when it is inconvenient or unpopular."),
            ("MHB-014", "Gandhari and the Cost of Blind Loyalty", "Family & Accountability", "When does protecting someone you love become enabling them?", "Gandhari's love, grief and loyalty exist alongside Duryodhana's destructive behavior.", "Love without accountability can unintentionally protect harmful choices."),
            ("MHB-015", "Kunti Reveals Karna's Birth", "Truth & Timing", "Can a truth revealed too late still repair what silence helped create?", "Kunti reveals Karna's identity only when the war is near.", "Truth has a timing dimension; delaying difficult conversations can make later choices much harder."),
            ("MHB-016", "Bhima and the Power of Controlled Strength", "Strength & Restraint", "Is strength about what you can do—or what you choose not to do?", "Bhima's immense physical power is repeatedly shaped by loyalty, anger and responsibility.", "Real strength includes emotional regulation and knowing when power should be restrained."),
            ("MHB-017", "Sanjaya Sees the War Clearly", "Perspective & Awareness", "What changes when you can observe conflict without being consumed by it?", "Sanjaya narrates the battlefield with unusual perspective and distance.", "Stepping outside immediate emotion can improve judgment and reveal patterns invisible from inside the conflict."),
            ("MHB-018", "The Pandavas in Exile", "Resilience & Identity", "Who are you when status, comfort and certainty are taken away?", "The Pandavas endure years of exile after losing their kingdom.", "Resilience is maintaining identity, learning and purpose while circumstances are temporarily against you."),
            ("MHB-019", "Nakula and Sahadeva: Quiet Strength", "Teamwork & Humility", "Why are the quiet contributors often essential to a strong team?", "The younger Pandavas receive less attention but contribute loyalty, skill and balance.", "Not every important contribution is visible; strong teams value dependable people, not only prominent leaders."),
            ("MHB-020", "The Final Journey of the Pandavas", "Detachment & Character", "What remains when titles, victories and possessions are finally left behind?", "The epic's closing journey strips away worldly achievements and tests character.", "Achievement matters, but character is what remains when status and possessions no longer define you."),
        ]
        for idea_id, title, pillar, hook, problem, safe_action in stories:
            con.execute(
                """INSERT OR IGNORE INTO ideas(
                     idea_id,pillar,series,working_title,hook,problem,safe_action,audience,priority,score,status,source_name,source_url,notes,created_at,channel_id)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    idea_id,
                    pillar,
                    "Mahabharata — Timeless Wisdom",
                    title,
                    hook,
                    problem,
                    safe_action,
                    "Global personal-growth audience",
                    "Backlog",
                    None,
                    "Backlog",
                    "Mahabharata source validation required before production",
                    None,
                    "Concept backlog only. Verify textual details and interpretation before scripting or animation.",
                    now,
                    2,
                ),
            )
    con.commit()


def _ctx(request: Request, **kwargs):
    return {"request": request, "now_year": datetime.now().year, **kwargs}


def install_content_hub(app) -> None:
    @app.get("/channels", response_class=HTMLResponse, name="channels")
    def channels_page(request: Request):
        con = _db_connect()
        try:
            _ensure_schema(con)
            channels = con.execute(
                """SELECT c.*,
                          (SELECT COUNT(*) FROM videos v WHERE v.channel_id=c.id) video_count,
                          (SELECT COUNT(*) FROM videos v WHERE v.channel_id=c.id AND v.status='Published') published_count,
                          (SELECT COUNT(*) FROM ideas i WHERE i.channel_id=c.id) idea_count
                   FROM channels c ORDER BY c.id"""
            ).fetchall()
            inbox_count = con.execute("SELECT COUNT(*) c FROM idea_inbox WHERE status='Inbox'").fetchone()["c"]
            return templates.TemplateResponse(request, "channels.html", _ctx(request, channels=channels, inbox_count=inbox_count))
        finally:
            con.close()

    @app.post("/channels/new", name="new_channel")
    def new_channel(name: str = Form(...), slug: str = Form(""), mission: str = Form("")):
        name = name.strip()
        if not name:
            raise HTTPException(400, "Channel name is required")
        clean_slug = (slug.strip() or name.lower()).replace(" ", "-")
        clean_slug = "".join(ch for ch in clean_slug if ch.isalnum() or ch in "-_").strip("-") or "channel"
        now = datetime.now().isoformat(timespec="seconds")
        con = _db_connect()
        try:
            _ensure_schema(con)
            base = clean_slug
            suffix = 2
            while con.execute("SELECT 1 FROM channels WHERE slug=?", (clean_slug,)).fetchone():
                clean_slug = f"{base}-{suffix}"; suffix += 1
            cur = con.execute(
                "INSERT INTO channels(slug,name,status,mission,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                (clean_slug, name, "Incubator", mission.strip() or None, now, now),
            )
            con.commit()
            return RedirectResponse(url=f"/channels/{cur.lastrowid}", status_code=303)
        finally:
            con.close()

    @app.get("/channels/{channel_id}", response_class=HTMLResponse, name="channel_detail")
    def channel_detail(request: Request, channel_id: int):
        con = _db_connect()
        try:
            _ensure_schema(con)
            channel = con.execute("SELECT * FROM channels WHERE id=?", (channel_id,)).fetchone()
            if not channel:
                raise HTTPException(404)
            videos = con.execute(
                "SELECT * FROM videos WHERE channel_id=? ORDER BY COALESCE(channel_video_no,number), number",
                (channel_id,),
            ).fetchall()
            ideas = con.execute(
                "SELECT * FROM ideas WHERE channel_id=? ORDER BY CASE WHEN status='In Production' THEN 1 ELSE 2 END, idea_id",
                (channel_id,),
            ).fetchall()
            latest_metrics = {}
            for video in videos:
                row = con.execute("SELECT * FROM metrics WHERE video_id=? ORDER BY id DESC LIMIT 1", (video["id"],)).fetchone()
                if row:
                    latest_metrics[video["id"]] = row
            return templates.TemplateResponse(
                request,
                "channel_detail.html",
                _ctx(request, channel=channel, videos=videos, ideas=ideas, latest_metrics=latest_metrics),
            )
        finally:
            con.close()

    @app.post("/channels/{channel_id}/update", name="update_channel")
    def update_channel(
        channel_id: int,
        name: str = Form(""), handle: str = Form(""), status: str = Form("Incubator"),
        mission: str = Form(""), tagline: str = Form(""), audience: str = Form(""),
        content_pillars: str = Form(""), format_strategy: str = Form(""), language_strategy: str = Form(""),
        visual_style: str = Form(""), source_policy: str = Form(""), notes: str = Form(""),
        youtube_channel_id: str = Form(""),
    ):
        now = datetime.now().isoformat(timespec="seconds")
        con = _db_connect()
        try:
            _ensure_schema(con)
            con.execute(
                """UPDATE channels SET name=?,handle=?,status=?,mission=?,tagline=?,audience=?,content_pillars=?,
                   format_strategy=?,language_strategy=?,visual_style=?,source_policy=?,notes=?,youtube_channel_id=?,updated_at=? WHERE id=?""",
                tuple((x.strip() or None) for x in [name,handle,status,mission,tagline,audience,content_pillars,format_strategy,language_strategy,visual_style,source_policy,notes,youtube_channel_id]) + (now, channel_id),
            )
            con.commit()
            return RedirectResponse(url=f"/channels/{channel_id}", status_code=303)
        finally:
            con.close()

    @app.post("/channels/{channel_id}/videos/new", name="new_channel_video")
    def new_channel_video(channel_id: int, topic: str = Form(...)):
        topic = topic.strip()
        if not topic:
            raise HTTPException(400, "Topic is required")
        now = datetime.now().isoformat(timespec="seconds")
        con = _db_connect()
        try:
            _ensure_schema(con)
            if not con.execute("SELECT 1 FROM channels WHERE id=?", (channel_id,)).fetchone():
                raise HTTPException(404)
            global_no = con.execute("SELECT COALESCE(MAX(number),0)+1 n FROM videos").fetchone()["n"]
            channel_no = con.execute("SELECT COALESCE(MAX(channel_video_no),0)+1 n FROM videos WHERE channel_id=?", (channel_id,)).fetchone()["n"]
            cur = con.execute(
                "INSERT INTO videos(number,channel_id,channel_video_no,topic,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                (global_no, channel_id, channel_no, topic, "Planning", now, now),
            )
            for order_no, (key, stage_name) in enumerate(PIPELINE, start=1):
                con.execute(
                    "INSERT OR IGNORE INTO stages(video_id,stage_key,stage_name,order_no,status) VALUES(?,?,?,?,?)",
                    (cur.lastrowid, key, stage_name, order_no, "Not Started"),
                )
            con.execute("UPDATE stages SET status='In Review' WHERE video_id=? AND stage_key='problem'", (cur.lastrowid,))
            con.commit()
            return RedirectResponse(url=f"/videos/{cur.lastrowid}", status_code=303)
        finally:
            con.close()

    @app.post("/channels/{channel_id}/ideas/new", name="new_channel_idea")
    def new_channel_idea(channel_id: int, title: str = Form(...), hook: str = Form(""), lesson: str = Form("")):
        title = title.strip()
        if not title:
            raise HTTPException(400, "Idea title is required")
        now = datetime.now().isoformat(timespec="seconds")
        con = _db_connect()
        try:
            _ensure_schema(con)
            count = con.execute("SELECT COUNT(*) c FROM ideas WHERE channel_id=?", (channel_id,)).fetchone()["c"] + 1
            idea_id = f"CH{channel_id}-{count:03d}"
            while con.execute("SELECT 1 FROM ideas WHERE idea_id=?", (idea_id,)).fetchone():
                count += 1; idea_id = f"CH{channel_id}-{count:03d}"
            con.execute(
                """INSERT INTO ideas(idea_id,working_title,hook,safe_action,status,created_at,channel_id)
                   VALUES(?,?,?,?,?,?,?)""",
                (idea_id, title, hook.strip() or None, lesson.strip() or None, "Backlog", now, channel_id),
            )
            con.commit()
            return RedirectResponse(url=f"/channels/{channel_id}", status_code=303)
        finally:
            con.close()

    @app.get("/idea-inbox", response_class=HTMLResponse, name="idea_inbox")
    def idea_inbox(request: Request):
        con = _db_connect()
        try:
            _ensure_schema(con)
            channels = con.execute("SELECT id,name FROM channels ORDER BY id").fetchall()
            ideas = con.execute(
                """SELECT x.*,c.name suggested_channel_name FROM idea_inbox x
                   LEFT JOIN channels c ON c.id=x.suggested_channel_id
                   ORDER BY CASE x.status WHEN 'Inbox' THEN 1 ELSE 2 END, x.id DESC"""
            ).fetchall()
            return templates.TemplateResponse(request, "idea_inbox.html", _ctx(request, channels=channels, ideas=ideas))
        finally:
            con.close()

    @app.post("/idea-inbox/new", name="new_inbox_idea")
    def new_inbox_idea(title: str = Form(...), thought: str = Form(""), suggested_channel_id: str = Form("")):
        now = datetime.now().isoformat(timespec="seconds")
        channel_id = int(suggested_channel_id) if suggested_channel_id.strip().isdigit() else None
        con = _db_connect()
        try:
            _ensure_schema(con)
            con.execute(
                "INSERT INTO idea_inbox(title,thought,suggested_channel_id,status,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                (title.strip(), thought.strip() or None, channel_id, "Inbox", now, now),
            )
            con.commit()
            return RedirectResponse(url="/idea-inbox", status_code=303)
        finally:
            con.close()

    @app.post("/idea-inbox/{idea_id}/assign", name="assign_inbox_idea")
    def assign_inbox_idea(idea_id: int, channel_id: int = Form(...)):
        now = datetime.now().isoformat(timespec="seconds")
        con = _db_connect()
        try:
            _ensure_schema(con)
            inbox = con.execute("SELECT * FROM idea_inbox WHERE id=?", (idea_id,)).fetchone()
            if not inbox:
                raise HTTPException(404)
            seq = con.execute("SELECT COUNT(*) c FROM ideas WHERE channel_id=?", (channel_id,)).fetchone()["c"] + 1
            code = f"CH{channel_id}-{seq:03d}"
            while con.execute("SELECT 1 FROM ideas WHERE idea_id=?", (code,)).fetchone():
                seq += 1; code = f"CH{channel_id}-{seq:03d}"
            con.execute(
                "INSERT INTO ideas(idea_id,working_title,problem,status,notes,created_at,channel_id) VALUES(?,?,?,?,?,?,?)",
                (code, inbox["title"], inbox["thought"], "Backlog", "Created from Global Idea Inbox", now, channel_id),
            )
            con.execute("UPDATE idea_inbox SET status='Assigned',suggested_channel_id=?,updated_at=? WHERE id=?", (channel_id, now, idea_id))
            con.commit()
            return RedirectResponse(url="/idea-inbox", status_code=303)
        finally:
            con.close()

    @app.get("/api/content/video/{video_id}/channel", name="video_channel_info")
    def video_channel_info(video_id: int):
        con = _db_connect()
        try:
            _ensure_schema(con)
            row = con.execute(
                """SELECT v.channel_id,v.channel_video_no,c.name channel_name,c.slug channel_slug
                   FROM videos v LEFT JOIN channels c ON c.id=v.channel_id WHERE v.id=?""",
                (video_id,),
            ).fetchone()
            if not row:
                raise HTTPException(404)
            return dict(row)
        finally:
            con.close()
