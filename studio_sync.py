from __future__ import annotations

from datetime import datetime


def sync_whatsapp_series(db_connect, ensure_stages):
    """Idempotently keep the WhatsApp mini-series and revised workflow in the Studio."""
    con = db_connect()
    now = datetime.now().isoformat(timespec="seconds")
    published_date = "2026-09-07"

    # Preserve YouTube Studio tags in the living database.
    video_columns = {row["name"] for row in con.execute("PRAGMA table_info(videos)").fetchall()}
    if "youtube_tags" not in video_columns:
        con.execute("ALTER TABLE videos ADD COLUMN youtube_tags TEXT")

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

    # Video #3 — Package Delivery Scam — published and fully documented.
    v3 = con.execute("SELECT * FROM videos WHERE number=3").fetchone()
    if v3:
        con.execute(
            """UPDATE videos SET title=?, description=?, hashtags=?, youtube_tags=?, pinned_comment=?, notes=?, updated_at=? WHERE id=?""",
            (
                "Package Delivery Scam Alert: Don’t Click That Text Link! #Shorts",
                "Got a text saying your package can't be delivered or that you need to pay a small redelivery fee? Do not use the link in the message. Open the carrier's official app or website yourself, check the tracking number there, and never enter personal or payment information through an unexpected text link.\n\nREAL-LIFE IQ — Smarter Choices for Real Life.",
                "#PackageScam #DeliveryScam #TextScam #Smishing #ScamAwareness #OnlineSafety #RealLifeIQ #Shorts",
                "package delivery scam, package scam text, delivery scam, fake delivery text, package tracking scam, smishing, text message scam, package redelivery scam, scam awareness, online safety, REAL-LIFE IQ",
                "Got a package-delivery text with a link? Don’t click it just because the message looks urgent or familiar. Open the carrier’s official app or website yourself and check the tracking number there.\n\nRule to remember: verify the delivery outside the text message before entering any personal or payment information.",
                "Published 2026-09-07. Final package-delivery scam Short. Core rule: verify independently through the carrier's official app or website rather than the inbound text link.",
                now, v3["id"]
            ),
        )
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
        hashtags4 = "#WhatsAppScam #VerificationCodeScam #WhatsAppSecurity #AccountTakeover #ScamAwareness #CyberSafety #OnlineSafety #RealLifeIQ #Shorts"
        tags4 = "WhatsApp verification code scam, WhatsApp scam, WhatsApp verification code, six digit code scam, WhatsApp account takeover, WhatsApp security, verification code scam, messaging scam, scam awareness, cyber safety, online safety, REAL-LIFE IQ"
        pinned4 = "Never share a WhatsApp verification code — even if the message appears to come from someone you know. If someone asks for the 6-digit code, verify that person another way before doing anything.\n\nRemember: receiving the code does not mean your account is already hacked. Sharing it is what can put your account at risk."
        con.execute(
            """UPDATE videos
               SET title=?, description=?, hashtags=?, youtube_tags=?, pinned_comment=?, problem=?, takeaway=?, notes=?, updated_at=?
               WHERE id=?""",
            (
                "WhatsApp Verification Code Scam: Never Share This 6-Digit Code! #Shorts",
                description4, hashtags4, tags4, pinned4,
                "A scammer tricks someone into sharing a WhatsApp 6-digit registration code by pretending to be a friend or claiming the code was sent by mistake. Sharing the code can allow the scammer to register the victim's WhatsApp number on another device and take over the account.",
                "Never share your WhatsApp registration code with anyone. If someone asks for it, verify the person through another known method.",
                "Published 2026-09-07. WhatsApp mini-series Part 1 — Protect. Receiving the code is not itself a takeover; sharing it creates the danger.",
                now, v4["id"]
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
    hashtags5 = "#WhatsAppHacked #WhatsAppRecovery #AccountRecovery #WhatsAppSecurity #AccountTakeover #ScamAwareness #CyberSafety #OnlineSafety #RealLifeIQ #Shorts"
    tags5 = "WhatsApp hacked, WhatsApp account recovery, WhatsApp hacked recovery, WhatsApp account takeover, recover WhatsApp account, WhatsApp verification code, WhatsApp security, WhatsApp scam, WhatsApp linked devices, two step verification WhatsApp, SIM swap, account recovery, scam awareness, cyber safety, online safety, REAL-LIFE IQ"
    pinned5 = "If your WhatsApp is taken over, remember: the scammer may control your WhatsApp session, but if you still control your phone number, you can reclaim the account. Re-register your number, enter the new verification code, then secure Linked Devices and turn on two-step verification.\n\nIf you can’t receive texts or calls on your number, contact your mobile carrier first."
    con.execute(
        """UPDATE videos
           SET title=?, description=?, hashtags=?, youtube_tags=?, pinned_comment=?, status='Final Ready', problem=?, takeaway=?, notes=?, upload_date=NULL, publish_date=NULL, updated_at=?
           WHERE id=?""",
        (
            "WhatsApp Hacked? How to Reclaim Your Account Fast #Shorts",
            description5, hashtags5, tags5, pinned5,
            "A viewer has lost control of a WhatsApp account and needs to understand why re-registration can recover it. If the viewer still controls the phone number, a fresh WhatsApp verification code proves control of that number and re-registers the account. If calls or texts no longer arrive, the mobile number or SIM may also be compromised and the carrier should be contacted first.",
            "If you still control your phone number, re-register it in WhatsApp with a new verification code, then remove unknown linked devices, enable two-step verification, and warn your contacts.",
            "WhatsApp mini-series Part 2 — Reclaim / Recovery. Final video approved. 6-slide technical recovery flow. Approved runtime: 36.89 seconds. Final file: whatsapp5_final_good_audio.mp4. Voice-over uses the user-approved natural MP3.",
            now, v5_id
        ),
    )
    for key in ("problem", "slides", "voice", "publishing", "final_video"):
        con.execute("UPDATE stages SET status='Approved', approved_at=COALESCE(approved_at, ?) WHERE video_id=? AND stage_key=?", (now, v5_id, key))
    con.execute("UPDATE stages SET status='In Review', approved_at=NULL WHERE video_id=? AND stage_key='published' AND status!='Approved'", (v5_id,))
    con.execute("UPDATE stages SET status='Not Started', approved_at=NULL WHERE video_id=? AND stage_key='metrics' AND status!='Approved'", (v5_id,))

    con.commit()
    con.close()
