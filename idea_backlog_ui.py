from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

import app as studio

app = studio.app
BASE_DIR = Path(__file__).resolve().parent

PUBLISHED_STATUSES = {"Published", "Completed", "Uploaded", "Final Published"}
IDEA_TERMINAL_STATUSES = PUBLISHED_STATUSES | {"Done", "Duplicate"}

# Current channel topics confirmed as already published. This supplements the older
# published_videos seed so backlog cleanup is durable even when the database is rebuilt.
RECENT_PUBLISHED_TITLES = [
    "Facebook Hacked Recovery",
    "Credit Card Lost or Stolen",
    "Lost Luggage at Airport",
    "Catalytic Converter Stolen",
    "Amazon Account Hacked",
]

# Ideas that are direct duplicates of videos already published on the channel.
PUBLISHED_IDEA_IDS = {
    "P001", "P002", "P003", "P004", "P005", "P006", "P008", "P009",
    "P012", "P013", "P061", "P062", "P063", "P064", "P065", "P066",
    "P068", "P071", "P088", "P090",
    "CYB-010", "CYB-013", "CYB-019", "CYB-025", "CYB-026", "CYB-051",
}

ACTIVE_PROJECTS = [
    {
        "idea_id": "ACTIVE-ATM-CARD",
        "pillar": "Financial Theft & Recovery",
        "series": "ATM Survival",
        "working_title": "Debit Card Swallowed by ATM",
        "hook": "ATM swallowed your debit card? Do this before you leave.",
        "problem": "An ATM retains the debit card and the viewer needs to protect the card/account while deciding whether the branch can safely return it.",
        "safe_action": "Record the ATM details, use the branch if it is open, lock or freeze the card, contact the issuing bank, monitor transactions, and replace the card if it cannot be safely returned.",
        "audience": "Debit-card users",
        "priority": "A+ / Make Soon",
        "score": 99,
        "status": "Slides Ready",
        "notes": "Eight approved individual slides are saved. Next phase: voice-over, then final video.",
    },
    {
        "idea_id": "ACTIVE-AIRTAG",
        "pillar": "Personal Safety & Tracking",
        "series": "Tracking Alert Survival",
        "working_title": "Unknown AirTag Moving With You",
        "hook": "Unknown AirTag moving with you? Don’t ignore it. Someone may be tracking you.",
        "problem": "A phone reports an unknown AirTag moving with the viewer and they need a safe way to locate, document, and disable it without confronting anyone.",
        "safe_action": "Open the alert, move to a safe public place if needed, use the phone to locate the tracker, check belongings and vehicle, contact someone trusted or police when appropriate, and disable the tracker safely.",
        "audience": "Smartphone users",
        "priority": "A+ / Make Soon",
        "score": 100,
        "status": "Slides Ready",
        "notes": "Eight approved individual slides are saved. Next phase: voice-over, then final video.",
    },
]

# Existing ideas to surface first in the editable priority queue.
INITIAL_PRIORITY_IDS = [
    "THFT-031",   # Find My shows stolen phone at a stranger's house
    "THFT-008",   # Car keys / key fob stolen
    "P069",       # Wallet stolen / missing
    "ACTIVE-ATM-CARD",
    "ACTIVE-AIRTAG",
]


def _columns(con, table: str) -> set[str]:
    return {row["name"] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}


def _norm(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def classify_subject(row) -> str:
    text = " ".join(
        str(row[k] or "")
        for k in ("working_title", "pillar", "series", "hook", "problem", "notes")
        if k in row.keys()
    ).lower()

    # Specific lanes first; generic scam/cyber terms come later.
    if any(x in text for x in ["teen", "student", "college", "child", "gaming", "scholarship", "fafsa", "youth"]):
        return "Youth & Student Safety"
    if any(x in text for x in ["airport", "airline", "luggage", "hotel", "travel", "rental-car", "passport"]):
        return "Travel Safety & Recovery"
    if any(x in text for x in ["investment", "crypto", "job", "recruiter", "employment", "task scam", "money mule", "scholarship"]):
        return "Jobs, Investment & Money Scams"
    if any(x in text for x in ["identity theft", "ssn", "social security", "driver’s license", "driver's license", "tax / employment identity", "benefit identity"]):
        return "Identity Theft"
    if any(x in text for x in ["car", "vehicle", "parking", "catalytic", "license plate", "key fob", "gas station", "garage opener"]):
        return "Vehicle & Parking Theft"
    if any(x in text for x in ["package", "porch", "mailroom", "mail theft", "house keys", "home", "hoa", "apartment", "resident"]):
        return "Home, Package & Community"
    if any(x in text for x in ["airtag", "tracking", "stalking", "harassment"]):
        return "Tracking & Personal Safety"
    if any(x in text for x in ["impersonation", "spoof", "grandparent", "fake lawyer", "fake support", "government", "jury-duty", "utility shutoff", "romance scam", "friend / boss"]):
        return "Impersonation"
    if any(x in text for x in ["hacked", "takeover", "account takeover", "password-reset", "password reset", "sim-swap", "sim swap", "mfa", "credential stuffing", "recovery phone", "recovery email"]):
        return "Hacking & Account Takeover"
    if any(x in text for x in ["malware", "ransomware", "phishing", "smishing", "vishing", "captcha", "data breach", "qr-code"]):
        return "Cybercrime & Phishing"
    if any(x in text for x in ["bank", "card", "payment", "wire", "gift card", "atm", "loan", "credit", "check", "zelle", "venmo", "cash app"]):
        return "Banking & Payment Fraud"
    if any(x in text for x in ["theft", "stolen", "snatch", "pickpocket", "smash-and-grab", "locker"]):
        return "Theft & Recovery"
    if any(x in text for x in ["scam", "fraud", "fake", "lottery", "sweepstakes"]):
        return "Scams & Fraud"
    return "Other Safety"


def _mark_published_from_seed(con) -> None:
    seed_path = BASE_DIR / "seed" / "published_videos.json"
    titles = []
    if seed_path.exists():
        try:
            payload = json.loads(seed_path.read_text(encoding="utf-8"))
            for item in payload.get("videos", []):
                titles.extend([item.get("topic"), item.get("title")])
        except Exception:
            pass
    titles.extend(RECENT_PUBLISHED_TITLES)
    normalized = [_norm(x) for x in titles if x]

    for idea in con.execute("SELECT * FROM ideas").fetchall():
        if idea["idea_id"] in PUBLISHED_IDEA_IDS:
            con.execute("UPDATE ideas SET status='Published', youtube_state='Published' WHERE id=?", (idea["id"],))
            continue
        name = _norm(idea["working_title"])
        # Conservative text reconciliation: only mark when the concept is a close textual match.
        if name and any(name == t or (len(name) > 18 and (name in t or t in name)) for t in normalized if len(t) > 10):
            con.execute("UPDATE ideas SET status='Published', youtube_state='Published' WHERE id=?", (idea["id"],))


def sync_idea_backlog() -> None:
    con = studio.db_connect()
    cols = _columns(con, "ideas")
    if "subject" not in cols:
        con.execute("ALTER TABLE ideas ADD COLUMN subject TEXT")
    if "priority_no" not in cols:
        con.execute("ALTER TABLE ideas ADD COLUMN priority_no INTEGER")
    if "youtube_state" not in cols:
        con.execute("ALTER TABLE ideas ADD COLUMN youtube_state TEXT")
    if "updated_at" not in cols:
        con.execute("ALTER TABLE ideas ADD COLUMN updated_at TEXT")

    now = datetime.now().isoformat(timespec="seconds")
    for item in ACTIVE_PROJECTS:
        existing = con.execute("SELECT id FROM ideas WHERE idea_id=?", (item["idea_id"],)).fetchone()
        if existing:
            con.execute(
                "UPDATE ideas SET pillar=?,series=?,working_title=?,hook=?,problem=?,safe_action=?,audience=?,priority=?,score=?,notes=COALESCE(notes,?),updated_at=? WHERE idea_id=?",
                (item["pillar"], item["series"], item["working_title"], item["hook"], item["problem"], item["safe_action"], item["audience"], item["priority"], item["score"], item["notes"], now, item["idea_id"]),
            )
        else:
            con.execute(
                """INSERT INTO ideas(idea_id,pillar,series,working_title,hook,problem,safe_action,audience,priority,score,status,notes,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (item["idea_id"], item["pillar"], item["series"], item["working_title"], item["hook"], item["problem"], item["safe_action"], item["audience"], item["priority"], item["score"], item["status"], item["notes"], now, now),
            )

    # Preserve the current approved state of the wallet project instead of duplicating it.
    con.execute(
        "UPDATE ideas SET status='Slides Ready', notes=COALESCE(notes,'') || CASE WHEN COALESCE(notes,'')='' THEN '' ELSE ' ' END || ?, updated_at=? WHERE idea_id='P069' AND status IN ('Backlog','Planning','Next')",
        ("Eight approved individual slides are saved. Next phase: voice-over, then final video.", now),
    )

    _mark_published_from_seed(con)

    # Fill the new subject taxonomy once, while preserving any later manual category edits.
    for row in con.execute("SELECT * FROM ideas").fetchall():
        subject = row["subject"] if "subject" in row.keys() else None
        if not subject:
            subject = classify_subject(row)
        ystate = row["youtube_state"] if "youtube_state" in row.keys() else None
        if not ystate:
            ystate = "Published" if row["status"] in PUBLISHED_STATUSES else "Not Published"
        con.execute("UPDATE ideas SET subject=?, youtube_state=?, updated_at=COALESCE(updated_at,?) WHERE id=?", (subject, ystate, now, row["id"]))

    # Seed a useful editable order once. After the user edits priorities, never overwrite it.
    ranked_count = con.execute("SELECT COUNT(*) c FROM ideas WHERE priority_no IS NOT NULL AND status NOT IN ('Published','Completed','Uploaded','Done','Duplicate')").fetchone()["c"]
    if ranked_count == 0:
        n = 1
        seen = set()
        for idea_id in INITIAL_PRIORITY_IDS:
            row = con.execute("SELECT id,status FROM ideas WHERE idea_id=?", (idea_id,)).fetchone()
            if row and row["status"] not in IDEA_TERMINAL_STATUSES:
                con.execute("UPDATE ideas SET priority_no=? WHERE id=?", (n, row["id"]))
                seen.add(row["id"]); n += 1
        rest = con.execute(
            """SELECT id FROM ideas WHERE status NOT IN ('Published','Completed','Uploaded','Done','Duplicate')
               AND id NOT IN ({})
               ORDER BY CASE WHEN priority LIKE 'A+%' THEN 1 WHEN priority LIKE 'A /%' OR priority LIKE 'A/%' THEN 2 ELSE 3 END,
                        score DESC, idea_id""".format(",".join("?" for _ in seen) if seen else "-1"),
            list(seen),
        ).fetchall()
        for row in rest:
            con.execute("UPDATE ideas SET priority_no=? WHERE id=?", (n, row["id"])); n += 1

    con.commit()
    con.close()


def _remove_old_idea_routes() -> None:
    old_names = {"ideas", "promote_idea"}
    app.router.routes = [r for r in app.router.routes if getattr(r, "name", None) not in old_names]


_remove_old_idea_routes()
sync_idea_backlog()


@app.get("/ideas", response_class=HTMLResponse, name="ideas")
def ideas_page(request: Request, q: str = "", status: str = "", subject: str = "", pillar: str = "", view: str = "unfinished"):
    con = studio.db_connect()
    sql = "SELECT * FROM ideas WHERE 1=1"
    args = []
    if view == "unfinished" and not status:
        sql += " AND status NOT IN ('Published','Completed','Uploaded','Done','Duplicate')"
    elif view == "published" and not status:
        sql += " AND status IN ('Published','Completed','Uploaded')"
    elif view == "done" and not status:
        sql += " AND status='Done'"
    elif view == "duplicates" and not status:
        sql += " AND status='Duplicate'"
    if q:
        sql += " AND (working_title LIKE ? OR problem LIKE ? OR hook LIKE ? OR notes LIKE ?)"
        args += [f"%{q}%"] * 4
    if status:
        sql += " AND status=?"; args.append(status)
    if subject:
        sql += " AND subject=?"; args.append(subject)
    if pillar:
        sql += " AND pillar=?"; args.append(pillar)
    sql += " ORDER BY CASE WHEN priority_no IS NULL THEN 1 ELSE 0 END, priority_no, subject, score DESC, idea_id"
    rows = con.execute(sql, args).fetchall()
    subjects = [r[0] for r in con.execute("SELECT DISTINCT subject FROM ideas WHERE subject IS NOT NULL ORDER BY subject")]
    pillars = [r[0] for r in con.execute("SELECT DISTINCT pillar FROM ideas WHERE pillar IS NOT NULL ORDER BY pillar")]
    statuses = [r[0] for r in con.execute("SELECT DISTINCT status FROM ideas WHERE status IS NOT NULL ORDER BY status")]
    counts = {
        "unfinished": con.execute("SELECT COUNT(*) c FROM ideas WHERE status NOT IN ('Published','Completed','Uploaded','Done','Duplicate')").fetchone()["c"],
        "published": con.execute("SELECT COUNT(*) c FROM ideas WHERE status IN ('Published','Completed','Uploaded')").fetchone()["c"],
        "done": con.execute("SELECT COUNT(*) c FROM ideas WHERE status='Done'").fetchone()["c"],
        "duplicates": con.execute("SELECT COUNT(*) c FROM ideas WHERE status='Duplicate'").fetchone()["c"],
        "subjects": con.execute("SELECT COUNT(DISTINCT subject) c FROM ideas WHERE status NOT IN ('Published','Completed','Uploaded','Done','Duplicate')").fetchone()["c"],
    }
    con.close()
    grouped = {}
    for row in rows:
        grouped.setdefault(row["subject"] or "Other Safety", []).append(row)
    return studio.templates.TemplateResponse(
        request,
        "ideas.html",
        studio.ctx(request, ideas=rows, grouped=grouped, subjects=subjects, pillars=pillars, statuses=statuses,
                   q=q, status=status, subject=subject, pillar=pillar, view=view, counts=counts),
    )


@app.post("/ideas/{idea_id}/priority", name="update_idea_priority")
def update_idea_priority(idea_id: int, priority_no: str = Form("")):
    con = studio.db_connect()
    target = con.execute("SELECT * FROM ideas WHERE id=?", (idea_id,)).fetchone()
    if not target:
        con.close(); return RedirectResponse(url="/ideas", status_code=303)

    active = con.execute(
        """SELECT id FROM ideas WHERE status NOT IN ('Published','Completed','Uploaded','Done','Duplicate')
           ORDER BY CASE WHEN priority_no IS NULL THEN 1 ELSE 0 END, priority_no,
                    CASE WHEN priority LIKE 'A+%' THEN 1 WHEN priority LIKE 'A /%' OR priority LIKE 'A/%' THEN 2 ELSE 3 END,
                    score DESC, idea_id"""
    ).fetchall()
    order = [r["id"] for r in active if r["id"] != idea_id]
    raw = priority_no.strip()
    if raw:
        try:
            desired = max(1, int(raw))
        except ValueError:
            desired = len(order) + 1
        order.insert(min(desired - 1, len(order)), idea_id)
    # blank means unranked; keep it out of the numbered sequence
    for pos, rid in enumerate(order, start=1):
        con.execute("UPDATE ideas SET priority_no=?, updated_at=? WHERE id=?", (pos, datetime.now().isoformat(timespec="seconds"), rid))
    if not raw:
        con.execute("UPDATE ideas SET priority_no=NULL, updated_at=? WHERE id=?", (datetime.now().isoformat(timespec="seconds"), idea_id))
    con.commit(); con.close()
    return RedirectResponse(url="/ideas?view=unfinished", status_code=303)


@app.post("/ideas/{idea_id}/metadata", name="update_idea_metadata")
def update_idea_metadata(idea_id: int, subject: str = Form(""), status: str = Form("")):
    con = studio.db_connect()
    subject = subject.strip() or None
    status = status.strip() or "Backlog"
    youtube_state = "Published" if status in PUBLISHED_STATUSES else "Not Published"
    con.execute("UPDATE ideas SET subject=?,status=?,youtube_state=?,updated_at=? WHERE id=?",
                (subject, status, youtube_state, datetime.now().isoformat(timespec="seconds"), idea_id))
    con.commit(); con.close()
    return RedirectResponse(url="/ideas?view=unfinished", status_code=303)


@app.post("/ideas/{idea_id}/quick-status", name="update_idea_quick_status")
def update_idea_quick_status(idea_id: int, status: str = Form(...), return_view: str = Form("unfinished")):
    if status not in {"Done", "Duplicate"}:
        return RedirectResponse(url="/ideas?view=unfinished", status_code=303)
    con = studio.db_connect()
    row = con.execute("SELECT id FROM ideas WHERE id=?", (idea_id,)).fetchone()
    if row:
        con.execute(
            "UPDATE ideas SET status=?,youtube_state='Not Published',priority_no=NULL,updated_at=? WHERE id=?",
            (status, datetime.now().isoformat(timespec="seconds"), idea_id),
        )
        con.commit()
    con.close()
    if return_view not in {"unfinished", "all", "published", "done", "duplicates"}:
        return_view = "unfinished"
    return RedirectResponse(url=f"/ideas?view={return_view}", status_code=303)


@app.post("/ideas/{idea_id}/promote", name="promote_idea")
def promote_idea(idea_id: int):
    con = studio.db_connect(); idea = con.execute("SELECT * FROM ideas WHERE id=?", (idea_id,)).fetchone()
    if not idea:
        con.close(); return RedirectResponse(url="/ideas", status_code=303)
    number = con.execute("SELECT COALESCE(MAX(number),0)+1 n FROM videos").fetchone()["n"]
    now = datetime.now().isoformat(timespec="seconds")
    cur = con.execute(
        "INSERT INTO videos(number,topic,title,status,problem,takeaway,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
        (number, idea["working_title"], idea["working_title"], "Problem Definition", idea["problem"], idea["safe_action"], f"Created from idea {idea['idea_id'] or idea['id']}", now, now),
    )
    studio.ensure_stages(con, cur.lastrowid)
    con.execute("UPDATE stages SET status='In Review' WHERE video_id=? AND stage_key='problem'", (cur.lastrowid,))
    con.execute("UPDATE ideas SET status='In Production', updated_at=? WHERE id=?", (now, idea_id))
    con.commit(); vid = cur.lastrowid; con.close()
    return RedirectResponse(url=f"/videos/{vid}", status_code=303)
