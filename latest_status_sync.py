from __future__ import annotations

from datetime import datetime


def sync_latest_status() -> None:
    """Keep the newest published REAL-LIFE IQ Short durable in the studio DB."""
    from app import db_connect, ensure_stages

    con = db_connect()
    now = datetime.now().isoformat(timespec="seconds")

    columns = {row["name"] for row in con.execute("PRAGMA table_info(videos)").fetchall()}
    if "youtube_tags" not in columns:
        con.execute("ALTER TABLE videos ADD COLUMN youtube_tags TEXT")
    if "voice_over_text" not in columns:
        con.execute("ALTER TABLE videos ADD COLUMN voice_over_text TEXT")

    record = {
        "number": 22,
        "topic": "Bank Jugging — Followed From the Bank",
        "title": "Bank Jugging? What To Do If Someone Follows You From the Bank",
        "published_date": "09-11-2026",
        "description": """Someone may watch you leave the bank, follow your car, and wait for the right moment to steal cash, your bag, or personal information. This crime is often called bank jugging.

In this short video, I break down what to do:
• Stay alert after leaving the bank
• Hide cash and avoid extra stops
• Watch for the same car following you
• Do not go home if you feel unsafe
• Drive to a police station or busy safe place
• If a theft happens, do not chase — call 911
• Call your bank fast and document every detail

The goal is simple: protect yourself first, then recover smart.

REAL-LIFE IQ — Verify first. Act second.""",
        "hashtags": "#BankJugging #PersonalSafety #CrimePrevention #TheftPrevention #SafetyTips #FraudAwareness #RealLifeIQ #StayAlert #BankSafety #ScamAwareness",
        "youtube_tags": "bank jugging, followed from bank, someone followed me from the bank, cash withdrawal safety, theft prevention, personal safety tips, what to do if followed, bank parking lot safety, robbery prevention, fraud prevention, real life iq",
        "pinned_comment": """If you think someone is following you after a bank visit, do not go home. Drive to a police station or a busy safe place and call 911. Your safety comes first.""",
        "problem": "A person is watched after a cash withdrawal, followed from the bank, and may be targeted for a daylight theft or robbery before realizing they were being tracked.",
        "takeaway": "Conceal cash, stay alert for repeat vehicles, avoid unnecessary stops, do not drive home if followed, move toward a safe public location or police station, call 911, and document/report the theft quickly.",
        "notes": "Published 09-11-2026. #22 Bank Jugging prevention + recovery Short. Final approved story uses 12 independent 9:16 slides with one consistent female character, realistic vehicles/props, broad-daylight theft scenario, and a recovery sequence. Final video validated at 1080x1920, 30 FPS, approximately 113.33 seconds; all 12 slides present once, 11 transitions visually checked, no overlap/bleed, full decode passed, and uploaded narration matched the embedded audio at approximately 0.99991 correlation.",
    }

    video = con.execute("SELECT * FROM videos WHERE number=?", (record["number"],)).fetchone()
    if video is None:
        cur = con.execute(
            "INSERT INTO videos(number,topic,status,created_at,updated_at) VALUES(?,?,?,?,?)",
            (record["number"], record["topic"], "Planning", now, now),
        )
        ensure_stages(con, cur.lastrowid)
        video_id = cur.lastrowid
    else:
        video_id = video["id"]
        ensure_stages(con, video_id)

    con.execute(
        """UPDATE videos
           SET topic=?, title=?, description=?, hashtags=?, youtube_tags=?, status='Published',
               problem=?, takeaway=?, upload_date=?, publish_date=?, pinned_comment=?, notes=?, updated_at=?
           WHERE id=?""",
        (
            record["topic"], record["title"], record["description"], record["hashtags"],
            record["youtube_tags"], record["problem"], record["takeaway"],
            record["published_date"], record["published_date"], record["pinned_comment"],
            record["notes"], now, video_id,
        ),
    )

    for key in ("problem", "slides", "voice", "publishing", "final_video", "published"):
        con.execute(
            """UPDATE stages
               SET status='Approved', approved_at=COALESCE(approved_at, ?)
               WHERE video_id=? AND stage_key=?""",
            (now, video_id, key),
        )

    con.execute(
        """UPDATE stages
           SET status='In Review', approved_at=NULL
           WHERE video_id=? AND stage_key='metrics' AND status!='Approved'""",
        (video_id,),
    )

    con.commit()
    con.close()
    print("Latest status sync complete: video #22 Bank Jugging marked Published.")


if __name__ == "__main__":
    sync_latest_status()
