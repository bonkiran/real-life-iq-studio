from __future__ import annotations

from datetime import datetime


def sync_whatsapp_series(db_connect, ensure_stages):
    """Idempotently keep the approved WhatsApp two-part mini-series in the Studio."""
    con = db_connect()
    now = datetime.now().isoformat(timespec="seconds")

    # Video #4 — Prevention. Move from problem review to slides once approved.
    v4 = con.execute("SELECT * FROM videos WHERE number=4").fetchone()
    if v4:
        con.execute(
            "UPDATE videos SET problem=?, takeaway=?, status=CASE WHEN status='Problem Definition' THEN 'Slides Verification' ELSE status END, updated_at=? WHERE id=?",
            (
                "A scammer tricks someone into sharing a WhatsApp 6-digit registration code by pretending to be a friend or claiming the code was sent by mistake. Sharing the code can allow the scammer to register the victim's WhatsApp number on another device and take over the account.",
                "Never share your WhatsApp registration code with anyone. If someone asks for it, verify the person through another known method.",
                now,
                v4["id"],
            ),
        )
        problem = con.execute("SELECT * FROM stages WHERE video_id=? AND stage_key='problem'", (v4["id"],)).fetchone()
        slides = con.execute("SELECT * FROM stages WHERE video_id=? AND stage_key='slides'", (v4["id"],)).fetchone()
        if problem and problem["status"] != "Approved":
            con.execute(
                "UPDATE stages SET status='Approved', approved_at=? WHERE id=?",
                (now, problem["id"]),
            )
        if slides and slides["status"] == "Not Started":
            con.execute("UPDATE stages SET status='In Review' WHERE id=?", (slides["id"],))

    # Video #5 — Recovery companion. Create only if it does not already exist.
    v5 = con.execute("SELECT * FROM videos WHERE number=5").fetchone()
    if not v5:
        cur = con.execute(
            """INSERT INTO videos(number,topic,title,status,problem,takeaway,notes,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                5,
                "WhatsApp Account Takeover Recovery",
                "WhatsApp Hacked? How to Reclaim Your Account Fast #Shorts",
                "Problem Definition",
                "A viewer has already lost access to their WhatsApp account after a takeover and needs a clear first recovery action. The recovery path is to re-register the same phone number in WhatsApp using a new verification code, which logs other devices out, then review linked devices, enable two-step verification, and warn contacts.",
                "Re-register your phone number in WhatsApp using the new verification code, then review linked devices, turn on two-step verification, and warn your contacts.",
                "WhatsApp mini-series Part 2 — Reclaim / Recovery. Companion to Video #4 prevention.",
                now,
                now,
            ),
        )
        ensure_stages(con, cur.lastrowid)
        con.execute(
            "UPDATE stages SET status='In Review' WHERE video_id=? AND stage_key='problem'",
            (cur.lastrowid,),
        )

    con.commit()
    con.close()
