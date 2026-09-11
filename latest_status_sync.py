from __future__ import annotations

from datetime import datetime


def sync_latest_status() -> None:
    """Keep the newest REAL-LIFE IQ production status durable in the studio DB."""
    from app import db_connect, ensure_stages

    con = db_connect()
    now = datetime.now().isoformat(timespec="seconds")

    columns = {row["name"] for row in con.execute("PRAGMA table_info(videos)").fetchall()}
    if "youtube_tags" not in columns:
        con.execute("ALTER TABLE videos ADD COLUMN youtube_tags TEXT")
    if "voice_over_text" not in columns:
        con.execute("ALTER TABLE videos ADD COLUMN voice_over_text TEXT")

    # #22 remains published.
    published = {
        "number": 22,
        "topic": "Bank Jugging — Followed From the Bank",
        "title": "Bank Jugging? What To Do If Someone Follows You From the Bank",
        "published_date": "09-11-2026",
        "problem": "A person is watched after a cash withdrawal, followed from the bank, and may be targeted for a daylight theft or robbery before realizing they were being tracked.",
        "takeaway": "Conceal cash, stay alert for repeat vehicles, avoid unnecessary stops, do not drive home if followed, move toward a safe public location or police station, call 911, and document/report the theft quickly.",
        "notes": "Published 09-11-2026. #22 Bank Jugging prevention + recovery Short.",
    }

    video = con.execute("SELECT * FROM videos WHERE number=?", (published["number"],)).fetchone()
    if video is None:
        cur = con.execute(
            "INSERT INTO videos(number,topic,status,created_at,updated_at) VALUES(?,?,?,?,?)",
            (published["number"], published["topic"], "Planning", now, now),
        )
        ensure_stages(con, cur.lastrowid)
        video_id = cur.lastrowid
    else:
        video_id = video["id"]
        ensure_stages(con, video_id)

    con.execute(
        """UPDATE videos SET topic=?, title=?, status='Published', problem=?, takeaway=?,
           upload_date=?, publish_date=?, notes=?, updated_at=? WHERE id=?""",
        (
            published["topic"], published["title"], published["problem"], published["takeaway"],
            published["published_date"], published["published_date"], published["notes"], now, video_id,
        ),
    )
    for key in ("problem", "slides", "voice", "publishing", "final_video", "published"):
        con.execute(
            "UPDATE stages SET status='Approved', approved_at=COALESCE(approved_at, ?) WHERE video_id=? AND stage_key=?",
            (now, video_id, key),
        )
    con.execute(
        "UPDATE stages SET status='In Review', approved_at=NULL WHERE video_id=? AND stage_key='metrics' AND status!='Approved'",
        (video_id,),
    )

    # #23 Package Theft is intentionally held after the actual approval render failed viewer playback / render QA.
    current = {
        "number": 23,
        "topic": "Package Stolen From Your Porch — Recovery + Prevention",
        "title": "Package Stolen From Your Porch? What To Do Next",
        "problem": "A package is confirmed delivered with a delivery photo, but the owner comes home and the package is gone. Recovery differs depending on whether usable doorbell/security-camera footage exists.",
        "takeaway": "Verify the delivery through official channels, preserve evidence, use the camera/no-camera recovery path, contact the seller/carrier and report confirmed theft when appropriate, then reduce future unattended-delivery risk.",
        "status": "HOLD — Render Rebuild Required",
        "notes": "QC Control Tower status 09-11-2026: source story/slides/voice are complete, but the approval MP4 failed CP11 Viewer Playback and CP12 Final Render Integrity. Confirmed defects: repeated/bouncing slide motion, narration/visual mismatches, wrong slide choices in parts of the timeline, and duplicate/repetitive ending visuals. No background rebuild should be implied. Next action: rebuild using the uploaded MP3 as the master timeline, then perform a complete start-to-finish viewer playback and final render integrity check before sending another approval cut.",
    }

    video = con.execute("SELECT * FROM videos WHERE number=?", (current["number"],)).fetchone()
    if video is None:
        cur = con.execute(
            "INSERT INTO videos(number,topic,status,created_at,updated_at) VALUES(?,?,?,?,?)",
            (current["number"], current["topic"], current["status"], now, now),
        )
        ensure_stages(con, cur.lastrowid)
        current_id = cur.lastrowid
    else:
        current_id = video["id"]
        ensure_stages(con, current_id)

    con.execute(
        """UPDATE videos SET topic=?, title=?, status=?, problem=?, takeaway=?, notes=?, updated_at=?
           WHERE id=?""",
        (
            current["topic"], current["title"], current["status"], current["problem"],
            current["takeaway"], current["notes"], now, current_id,
        ),
    )

    # Upstream work is approved. Final-video stage is explicitly back in review.
    for key in ("problem", "slides", "voice"):
        con.execute(
            "UPDATE stages SET status='Approved', approved_at=COALESCE(approved_at, ?) WHERE video_id=? AND stage_key=?",
            (now, current_id, key),
        )
    con.execute(
        "UPDATE stages SET status='Not Started', approved_at=NULL WHERE video_id=? AND stage_key='publishing'",
        (current_id,),
    )
    con.execute(
        "UPDATE stages SET status='In Review', approved_at=NULL, notes=? WHERE video_id=? AND stage_key='final_video'",
        (
            "CP11 Viewer Playback FAILED; CP12 Final Render Integrity FAILED. Rebuild required before approval.",
            current_id,
        ),
    )
    for key in ("published", "metrics"):
        con.execute(
            "UPDATE stages SET status='Not Started', approved_at=NULL WHERE video_id=? AND stage_key=?",
            (current_id, key),
        )

    con.commit()
    con.close()
    print("Latest status sync complete: #22 Published; #23 Package Theft on HOLD for render rebuild/QC.")


if __name__ == "__main__":
    sync_latest_status()
