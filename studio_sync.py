from __future__ import annotations

from datetime import datetime


def sync_whatsapp_series(db_connect, ensure_stages):
    """Idempotently keep the WhatsApp mini-series and revised workflow in the Studio."""
    con = db_connect()
    now = datetime.now().isoformat(timespec="seconds")
    published_date = "2026-09-07"

    # Workflow V2: prepare the publishing package BEFORE final-video assembly.
    stage_order = {
        "problem": (1, "Problem Definition"),
        "slides": (2, "Slides Verification"),
        "voice": (3, "Voice-over Verification"),
        "publishing": (4, "Publishing Plan"),
        "final_video": (5, "Final Video"),
        "published": (6, "Published"),
        "metrics": (7, "Metrics"),
    }
    for key, (order_no, stage_name) in stage_order.items():
        con.execute(
            "UPDATE stages SET order_no=?, stage_name=? WHERE stage_key=?",
            (order_no, stage_name, key),
        )

    def mark_published(video_number: int):
        video = con.execute("SELECT * FROM videos WHERE number=?", (video_number,)).fetchone()
        if not video:
            return None
        con.execute(
            """UPDATE videos
               SET status='Published',
                   upload_date=COALESCE(upload_date, ?),
                   publish_date=COALESCE(publish_date, ?),
                   updated_at=?
               WHERE id=?""",
            (published_date, published_date, now, video["id"]),
        )
        for key in ("problem", "slides", "voice", "publishing", "final_video", "published"):
            con.execute(
                """UPDATE stages
                   SET status='Approved', approved_at=COALESCE(approved_at, ?)
                   WHERE video_id=? AND stage_key=?""",
                (now, video["id"], key),
            )
        con.execute(
            """UPDATE stages
               SET status='In Review', approved_at=NULL
               WHERE video_id=? AND stage_key='metrics' AND status!='Approved'""",
            (video["id"],),
        )
        return video["id"]

    # Video #3 — Package Delivery Scam is now published.
    mark_published(3)

    # Video #4 — Prevention. Keep its approved publishing package populated.
    v4 = con.execute("SELECT * FROM videos WHERE number=4").fetchone()
    if v4:
        description4 = """Did someone ask for the 6-digit WhatsApp verification code sent to your phone?

Do not share it.

Scammers may pretend to be a friend and say the code was sent to you by mistake. If you send that code, they may be able to take over your WhatsApp account.

Before responding:
✅ Never share your verification code
✅ Pause and verify the person another way
✅ If it seems suspicious, ignore, block, and report

Protect your account before it’s taken over.

REAL-LIFE IQ — Smarter Choices for Real Life."""
        hashtags4 = "#WhatsAppScam #VerificationCodeScam #WhatsAppSecurity #AccountTakeover #TextScam #ScamAwareness #OnlineSafety #CyberSafety #RealLifeIQ #Shorts"
        con.execute(
            """UPDATE videos
               SET title=?, description=?, hashtags=?, problem=?, takeaway=?, updated_at=?
               WHERE id=?""",
            (
                "WhatsApp Verification Code Scam: Never Share This 6-Digit Code! #Shorts",
                description4,
                hashtags4,
                "A scammer tricks someone into sharing a WhatsApp 6-digit registration code by pretending to be a friend or claiming the code was sent by mistake. Sharing the code can allow the scammer to register the victim's WhatsApp number on another device and take over the account.",
                "Never share your WhatsApp registration code with anyone. If someone asks for it, verify the person through another known method.",
                now,
                v4["id"],
            ),
        )
    mark_published(4)

    # Video #5 — Recovery companion. Create if needed, then keep its pre-production
    # publishing package populated so it can be reviewed before slides/audio/video.
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
        v5_id = cur.lastrowid
        con.execute(
            "UPDATE stages SET status='In Review' WHERE video_id=? AND stage_key='problem'",
            (v5_id,),
        )
    else:
        v5_id = v5["id"]

    description5 = """Has your WhatsApp account been taken over?

Here’s what to do first:

✅ Open WhatsApp and re-register your phone number

✅ Enter the new 6-digit verification code

✅ Check Linked Devices and remove anything suspicious

✅ Enable two-step verification

✅ Warn your contacts that your account was compromised

Act quickly to regain control and protect your account.

REAL-LIFE IQ — Smarter Choices for Real Life."""
    hashtags5 = "#WhatsAppHacked #WhatsAppRecovery #AccountRecovery #WhatsAppSecurity #ScamAwareness #CyberSafety #OnlineSafety #RealLifeIQ #Shorts"
    con.execute(
        """UPDATE videos
           SET title=?, description=?, hashtags=?, problem=?, takeaway=?, updated_at=?
           WHERE id=?""",
        (
            "WhatsApp Hacked? How to Reclaim Your Account Fast #Shorts",
            description5,
            hashtags5,
            "A viewer has already lost access to their WhatsApp account after a takeover and needs a clear first recovery action. The recovery path is to re-register the same phone number in WhatsApp using a new verification code, which logs other devices out, then review linked devices, enable two-step verification, and warn contacts.",
            "Re-register your phone number in WhatsApp using the new verification code, then review linked devices, turn on two-step verification, and warn your contacts.",
            now,
            v5_id,
        ),
    )

    con.commit()
    con.close()
