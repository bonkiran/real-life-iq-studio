from __future__ import annotations

from datetime import datetime


def sync_whatsapp_series(db_connect, ensure_stages):
    """Idempotently keep approved REAL-LIFE IQ production records in the Studio."""
    con = db_connect()
    now = datetime.now().isoformat(timespec="seconds")

    # Living-schema migrations for fields added after the first Studio release.
    video_columns = {row["name"] for row in con.execute("PRAGMA table_info(videos)").fetchall()}
    if "youtube_tags" not in video_columns:
        con.execute("ALTER TABLE videos ADD COLUMN youtube_tags TEXT")
    if "voice_over_text" not in video_columns:
        con.execute("ALTER TABLE videos ADD COLUMN voice_over_text TEXT")

    # Workflow V2: publishing package is prepared before final-video assembly.
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

    def get_or_create_video(number: int, topic: str):
        video = con.execute("SELECT * FROM videos WHERE number=?", (number,)).fetchone()
        if video:
            return video
        cur = con.execute(
            "INSERT INTO videos(number,topic,status,created_at,updated_at) VALUES(?,?,?,?,?)",
            (number, topic, "Planning", now, now),
        )
        ensure_stages(con, cur.lastrowid)
        return con.execute("SELECT * FROM videos WHERE id=?", (cur.lastrowid,)).fetchone()

    def mark_published(video_number: int, published_date: str):
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

    # Video #3 — Package Delivery Scam.
    v3 = get_or_create_video(3, "Package Delivery Scam")
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
    mark_published(3, "2026-09-07")

    # Video #4 — WhatsApp Verification Code Scam.
    v4 = get_or_create_video(4, "WhatsApp Verification Code Scam")
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
    mark_published(4, "2026-09-07")

    # Video #5 — WhatsApp Account Takeover Recovery. Final-ready; do not mark published until user confirms.
    v5 = get_or_create_video(5, "WhatsApp Account Takeover Recovery")
    description5 = """Has your WhatsApp account been taken over?

If you still control your phone number, you may be able to reclaim your account by re-registering that same number in WhatsApp.

Here’s what to do:

✅ Open WhatsApp and enter your phone number again
✅ Enter the new 6-digit verification code
✅ This re-registers the account and logs the attacker out
✅ If you can’t receive texts or calls, contact your mobile carrier first
✅ Check Linked Devices and remove anything unfamiliar
✅ Turn on two-step verification
✅ Warn your contacts that your account was compromised

Act fast, reclaim it, and secure it.

REAL-LIFE IQ — Smarter Choices for Real Life."""
    hashtags5 = "#WhatsAppHacked #WhatsAppRecovery #AccountRecovery #WhatsAppSecurity #AccountTakeover #ScamAwareness #CyberSafety #OnlineSafety #RealLifeIQ #Shorts"
    tags5 = "WhatsApp hacked, WhatsApp account recovery, WhatsApp hacked recovery, WhatsApp account takeover, recover WhatsApp account, WhatsApp verification code, WhatsApp security, WhatsApp scam, WhatsApp linked devices, two step verification WhatsApp, SIM swap, account recovery, scam awareness, cyber safety, online safety, REAL-LIFE IQ"
    pinned5 = "If your WhatsApp is taken over, remember: the scammer may control your WhatsApp session, but if you still control your phone number, you can reclaim the account. Re-register your number, enter the new verification code, then secure Linked Devices and turn on two-step verification.\n\nIf you can’t receive texts or calls on your number, contact your mobile carrier first."
    voice5 = "If your WhatsApp account was taken over, don’t panic. If you still control your phone number, you can take it back. WhatsApp uses your phone number as your account identity. Open WhatsApp and enter your number again. When you receive the new six-digit verification code, enter it. That re-registers your account and logs the scammer out. If you can’t receive texts or calls, contact your carrier first, because your SIM may also be compromised. Then secure your account: remove unknown linked devices, turn on two-step verification, and warn your contacts. Act fast, reclaim it, and secure it. REAL-LIFE IQ."
    con.execute(
        """UPDATE videos
           SET title=?, description=?, hashtags=?, youtube_tags=?, pinned_comment=?, voice_over_text=?, status='Final Ready', problem=?, takeaway=?, notes=?, upload_date=NULL, publish_date=NULL, updated_at=?
           WHERE id=?""",
        (
            "WhatsApp Hacked? How to Reclaim Your Account Fast #Shorts",
            description5, hashtags5, tags5, pinned5, voice5,
            "A viewer has lost control of a WhatsApp account and needs to understand why re-registration can recover it. If the viewer still controls the phone number, a fresh WhatsApp verification code proves control of that number and re-registers the account. If calls or texts no longer arrive, the mobile number or SIM may also be compromised and the carrier should be contacted first.",
            "If you still control your phone number, re-register it in WhatsApp with a new verification code, then remove unknown linked devices, enable two-step verification, and warn your contacts.",
            "WhatsApp mini-series Part 2 — Reclaim / Recovery. Final video approved. 6-slide technical recovery flow. Approved runtime: 36.89 seconds. Final file: whatsapp5_final_good_audio.mp4. Voice-over uses the user-approved natural MP3.",
            now, v5["id"]
        ),
    )
    for key in ("problem", "slides", "voice", "publishing", "final_video"):
        con.execute("UPDATE stages SET status='Approved', approved_at=COALESCE(approved_at, ?) WHERE video_id=? AND stage_key=?", (now, v5["id"], key))
    con.execute("UPDATE stages SET status='In Review', approved_at=NULL WHERE video_id=? AND stage_key='published' AND status!='Approved'", (v5["id"],))
    con.execute("UPDATE stages SET status='Not Started', approved_at=NULL WHERE video_id=? AND stage_key='metrics' AND status!='Approved'", (v5["id"],))

    # Video #6 — Gas Station Theft. Published 2026-09-08.
    v6 = get_or_create_video(6, "Gas Station Theft — Lock Your Car Before You Pump")
    description6 = """A quick stop for gas can create an easy opportunity for theft if your car is left unlocked.

In this real-world scenario, the driver steps inside the gas station for only a minute while valuables are left visible inside the car. Someone watching nearby can act within seconds.

Before walking away from your vehicle:

✅ Lock every door
✅ Take your purse, phone, wallet, and other valuables with you
✅ Avoid leaving valuables visible inside the car

Rule to remember: Lock the car and take your valuables with you.

REAL-LIFE IQ — Smarter Choices for Real Life."""
    hashtags6 = "#GasStationSafety #CarTheft #TheftPrevention #VehicleSafety #SafetyTips #CrimePrevention #RealLifeIQ #Shorts"
    tags6 = "gas station theft, gas station safety, car theft prevention, vehicle theft, purse theft, theft prevention tips, car safety tips, gas pump safety, parking lot theft, prevent car theft, vehicle safety, everyday safety, crime prevention, safety awareness, REAL-LIFE IQ"
    pinned6 = "Running inside the gas station for “just a minute” is enough time for someone to grab valuables from an unlocked car.\n\nBefore you walk away: lock the doors and take your purse, phone, wallet, and other valuables with you. Small habit. Big protection."
    voice6 = "You stop for gas and leave your car unlocked. Then you run inside the store for just a minute. But someone may already be watching for an easy opportunity. An unlocked door and visible valuables can make your car an easy target. The theft can happen in seconds, and when you come back, your purse, phone, or wallet may already be gone. Rule to remember: lock the car and take your valuables with you. REAL-LIFE IQ."
    con.execute(
        """UPDATE videos
           SET topic=?, title=?, description=?, hashtags=?, youtube_tags=?, pinned_comment=?, voice_over_text=?, problem=?, takeaway=?, notes=?, updated_at=?
           WHERE id=?""",
        (
            "Gas Station Theft — Lock Your Car Before You Pump",
            "Gas Station Theft: Lock Your Car Before You Pump #Shorts",
            description6, hashtags6, tags6, pinned6, voice6,
            "Drivers sometimes leave a vehicle unlocked while pumping gas or stepping briefly into a convenience store. An unlocked vehicle with visible valuables can create an easy theft opportunity within seconds.",
            "Lock the vehicle whenever you step away and take your purse, phone, wallet, and other valuables with you.",
            "Published 2026-09-08. Approved 6-slide real-world gas-station scenario. Continuity QA corrected fuel-door placement, passenger-side purse location, thief entry through the same passenger door, and final REAL-LIFE IQ logo mug. Final video: REAL_LIFE_IQ_06_Gas_Station_Theft_APPROVED.mp4. Approved voice-over MP3: Car Theft Risk.mp3.",
            now, v6["id"]
        ),
    )
    mark_published(6, "2026-09-08")

    # Video #7 — Fake Job Text. Published 2026-09-08.
    v7 = get_or_create_video(7, "Fake Job Text — Asked to Reply YES?")
    description7 = """Got an unexpected text offering a remote job with great pay, flexible hours, and little or no experience required?

Slow down before responding.

Watch for red flags such as:

✅ Being asked to reply YES or move the conversation to WhatsApp
✅ Requests for your Social Security number or bank information
✅ Being asked to pay a processing, training, or application fee
✅ A job you cannot verify on the company’s official careers website

Instead of trusting the text, find the company’s official website yourself and confirm that the job actually exists.

Rule to remember: Never pay money to get a job. Verify first.

REAL-LIFE IQ — Smarter Choices for Real Life."""
    hashtags7 = "#JobScam #FakeJobText #EmploymentScam #JobSearchSafety #ScamAwareness #CyberSafety #OnlineSafety #RealLifeIQ #Shorts"
    tags7 = "fake job text, fake job scam, job text scam, employment scam, remote job scam, WhatsApp job scam, fake recruiter, job offer scam, job search safety, social security number scam, SSN scam, bank information scam, processing fee scam, scam awareness, cyber safety, online safety, REAL-LIFE IQ"
    pinned7 = "An unexpected job offer with great pay can be tempting, but don’t let urgency replace verification.\n\nIf a recruiter asks for your SSN, bank details, or money before you’re hired, stop. Find the company’s official website yourself and verify the position through its real careers page.\n\nRule: Never pay money to get a job. Verify first."
    voice7 = "An unexpected text offers you a remote job with flexible hours and great pay. Forty-two dollars an hour, fast hiring, and no experience required? Slow down. If they ask you to reply YES or move to WhatsApp, that still does not prove the recruiter is real. Red flags include requests for your Social Security number, bank details, or a processing fee. Check the company’s official careers page yourself. Never pay money to get a job. Verify first. REAL-LIFE IQ."
    con.execute(
        """UPDATE videos
           SET topic=?, title=?, description=?, hashtags=?, youtube_tags=?, pinned_comment=?, voice_over_text=?, problem=?, takeaway=?, notes=?, updated_at=?
           WHERE id=?""",
        (
            "Fake Job Text — Asked to Reply YES?",
            "Fake Job Text Scam: Asked to Reply YES? #Shorts",
            description7, hashtags7, tags7, pinned7, voice7,
            "Unexpected job texts can use unusually high pay, fast hiring, little experience required, WhatsApp handoffs, requests for sensitive personal information, or upfront fees to pressure job seekers before they verify the employer or position.",
            "Do not trust the inbound text alone. Find the company’s official careers page yourself, verify that the job exists, and never pay money to get a job.",
            "Published 2026-09-08. Approved 6-slide fake-job-text story. Slide 3 corrected so the character holds the phone naturally without an extra hand; Slide 4 includes SSN; Slide 6 uses a physical REAL-LIFE IQ logo mug. Final video: Video_07_Fake_Job_Text.mp4. Approved audio: fakeJobAlert.mp3. Runtime: 28.44 seconds, 1080x1920, 30 fps.",
            now, v7["id"]
        ),
    )
    mark_published(7, "2026-09-08")

    con.commit()
    con.close()
