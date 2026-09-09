from __future__ import annotations

from datetime import datetime


def sync_whatsapp_series(db_connect, ensure_stages):
    """Keep REAL-LIFE IQ production records synchronized with published Shorts."""
    con = db_connect()
    now = datetime.now().isoformat(timespec="seconds")

    # Living-schema migrations.
    columns = {row["name"] for row in con.execute("PRAGMA table_info(videos)").fetchall()}
    if "youtube_tags" not in columns:
        con.execute("ALTER TABLE videos ADD COLUMN youtube_tags TEXT")
    if "voice_over_text" not in columns:
        con.execute("ALTER TABLE videos ADD COLUMN voice_over_text TEXT")

    stage_order = {
        "problem": (1, "Problem Definition"),
        "slides": (2, "Slides Verification"),
        "voice": (3, "Voice-over Verification"),
        "publishing": (4, "Publishing Plan"),
        "final_video": (5, "Final Video"),
        "published": (6, "Published"),
        "metrics": (7, "Metrics"),
    }
    for key, (order_no, name) in stage_order.items():
        con.execute(
            "UPDATE stages SET order_no=?, stage_name=? WHERE stage_key=?",
            (order_no, name, key),
        )

    records = {
        1: ("Bank Scam", "Your Bank Says an $846 Purchase Is Pending. What Do You Do?", "09-06-2026"),
        2: ("Fake Toll Text", "Fake Toll Payment Text Scam: Don’t Click That Link! #Shorts", "09-06-2026"),
        3: ("Package Delivery Scam", "Package Delivery Scam Alert: Don’t Click That Text Link! #Shorts", "09-07-2026"),
        4: ("WhatsApp Verification Code Scam", "WhatsApp Verification Code Scam: Never Share This 6-Digit Code! #Shorts", "09-07-2026"),
        5: ("WhatsApp Account Takeover Recovery", "WhatsApp Hacked? How to Reclaim Your Account Fast #Shorts", "09-08-2026"),
        6: ("Gas Station Theft — Lock Your Car Before You Pump", "Gas Station Theft: Lock Your Car Before You Pump #Shorts", "09-08-2026"),
        7: ("Fake Job Text — Asked to Reply YES?", "Fake Job Text Scam: Asked to Reply YES? #Shorts", "09-08-2026"),
        8: ("ATM Skimmer Warning", "ATM Skimmer Warning: Check This Before You Insert Your Card #Shorts", "09-08-2026"),
        9: ("AI Voice-Cloning Emergency Call Scam", "“Mom, I’m in Trouble!” — Could That Voice Be AI? #Shorts", "09-08-2026"),
        10: ("FTC Scam Watch — Latest FTC Data Available", "FTC Scam Watch: $15.9 Billion Reported Lost to Fraud #Shorts", "09-08-2026"),
        11: ("WhatsApp Investment Group — Social Proof Scam", "WhatsApp Investment Group Full of “Winners”? Watch These Red Flags #Shorts", "09-08-2026"),
    }

    def get_or_create(number, topic):
        row = con.execute("SELECT * FROM videos WHERE number=?", (number,)).fetchone()
        if row:
            return row
        cur = con.execute(
            "INSERT INTO videos(number,topic,status,created_at,updated_at) VALUES(?,?,?,?,?)",
            (number, topic, "Planning", now, now),
        )
        ensure_stages(con, cur.lastrowid)
        return con.execute("SELECT * FROM videos WHERE id=?", (cur.lastrowid,)).fetchone()

    def mark_published(video_id, topic, title, date):
        con.execute(
            """UPDATE videos
               SET topic=?, title=?, status='Published',
                   upload_date=?, publish_date=?, updated_at=?
               WHERE id=?""",
            (topic, title, date, date, now, video_id),
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

    for number, (topic, title, date) in records.items():
        video = get_or_create(number, topic)
        mark_published(video["id"], topic, title, date)

    # Populate approved production details for the newest Shorts.
    v8 = con.execute("SELECT id FROM videos WHERE number=8").fetchone()
    con.execute(
        """UPDATE videos SET description=?, hashtags=?, youtube_tags=?,
           pinned_comment=?, voice_over_text=?, problem=?, takeaway=?, notes=?, updated_at=?
           WHERE id=?""",
        (
            "ATM skimmers can be hard to spot. Before inserting your card, inspect the reader and give it a gentle tug. If it feels loose, raised, or unusual, do not use it. Cover the keypad when entering your PIN and look for anything unusual that could hide a camera. Whenever possible, use ATMs inside banks or other trusted locations.\n\nREAL-LIFE IQ — Smarter Choices for Real Life.",
            "#ATMSkimmer #ATMScam #CardSkimming #FraudPrevention #ScamAwareness #CyberSafety #OnlineSafety #RealLifeIQ #Shorts",
            "ATM skimmer, ATM skimming, card skimmer, ATM scam, card skimming scam, ATM safety, debit card fraud, credit card fraud, cover your PIN, fraud prevention, scam awareness, cyber safety, online safety, REAL-LIFE IQ",
            "Have you ever checked an ATM for a skimmer before using it?\n\nQuick rule: Check the reader. Cover your PIN. Use trusted ATMs.\n\nStay alert and share this with someone who uses ATMs.\nREAL-LIFE IQ — Smarter Choices for Real Life.",
            "ATM skimmers can be hard to spot. Before inserting your card, check the reader. Give it a gentle tug—if it feels loose, raised, or unusual, don't use it. When entering your PIN, cover the keypad with your hand and look for anything unusual that could hide a camera. Whenever possible, use ATMs inside banks or trusted locations. Remember: inspect the machine, cover your PIN, and stay alert. REAL-LIFE IQ — Smarter Choices for Real Life.",
            "ATM skimmers and hidden cameras can capture card data and PINs when a machine has been tampered with.",
            "Inspect the reader, cover your PIN, and prefer ATMs inside banks or trusted locations.",
            "Published 09-08-2026. Approved 6-slide ATM skimmer warning Short.",
            now,
            v8["id"],
        ),
    )

    v9 = con.execute("SELECT id FROM videos WHERE number=9").fetchone()
    con.execute(
        """UPDATE videos SET description=?, hashtags=?, youtube_tags=?,
           pinned_comment=?, voice_over_text=?, problem=?, takeaway=?, notes=?, updated_at=?
           WHERE id=?""",
        (
            "A call sounds exactly like your child: “Mom, I’m in trouble. I need money now.” But the voice may not be real.\n\nAI can clone a convincing voice from just seconds of audio.\n\nProtect yourself:\n• Don’t panic or send money immediately\n• Hang up and call your loved one directly\n• Use a number you already know\n• Create a family safe word\n• Verify the person, not just the voice\n\nREAL-LIFE IQ — Smarter Choices for Real Life.",
            "#AIVoiceScam #VoiceCloning #ScamAwareness #AIScam #FraudPrevention #FamilySafety #OnlineSafety #RealLifeIQ #Shorts",
            "AI voice scam, AI voice cloning, voice cloning scam, family emergency scam, grandparent scam, fake emergency call, artificial intelligence scam, AI fraud, scam awareness, family safe word, fraud prevention, cyber safety, Real Life IQ",
            "If someone you love called saying they were in trouble, would you recognize an AI-cloned voice?\n\nBest protection: Hang up. Call them directly. And have a family safe word.\nVerify the person — not the voice.\nREAL-LIFE IQ — Smarter Choices for Real Life.",
            "A call from your child says, ‘Mom, I’m in trouble. I need money now.’ It sounds exactly like them—but don’t panic. AI can clone a voice from seconds of audio taken from social media, videos, or voicemail. Stop and verify. Hang up, then call your child directly using the number you already know. Better yet, create a family safe word. If the caller can’t answer it, don’t send money. Remember: verify the person, not the voice. REAL-LIFE IQ — Smarter Choices for Real Life.",
            "AI voice cloning can make an emergency scam sound like a real loved one and pressure families to send money immediately.",
            "Hang up, call your loved one using a number you already know, and use a family safe word.",
            "Published 09-08-2026. Final video 1080x1920, 28.83 seconds, 30 FPS, H.264 + AAC; all 6 slides and full narration validated.",
            now,
            v9["id"],
        ),
    )

    v10 = con.execute("SELECT id FROM videos WHERE number=10").fetchone()
    con.execute(
        """UPDATE videos SET description=?, hashtags=?, youtube_tags=?,
           pinned_comment=?, voice_over_text=?, problem=?, takeaway=?, notes=?, updated_at=?
           WHERE id=?""",
        (
            "3 million fraud reports. $15.9 billion in reported losses.\n\nAccording to the latest official FTC data available, consumers reported major fraud losses in 2025:\n\n• $15.9 billion total reported fraud losses\n• $7.9 billion lost to investment scams\n• 1+ million imposter scam reports\n• $3.5 billion lost to imposter scams\n• $2.1 billion lost to scams that started on social media\n• Social-media scam losses were about 8× higher than in 2020\n\nThese are reported losses, so actual losses may be higher.\n\nOfficial FTC sources are included in the published YouTube description.\n\nREAL-LIFE IQ — Verify first. Act second.",
            "#FTC #ScamAlert #ScamAwareness #FraudPrevention #Fraud #InvestmentScam #ImposterScam #SocialMediaScam #OnlineSafety #RealLifeIQ #Shorts",
            "FTC scam data, FTC scam alert, FTC fraud statistics, fraud statistics 2025, scam awareness, fraud prevention, investment scam, investment fraud, imposter scam, social media scam, online scams, consumer fraud, ReportFraud FTC, cyber safety, online safety, Real Life IQ",
            "$15.9 BILLION in reported fraud losses.\n\nWhich number surprised you most?\n\nRemember: Pause before paying. Verify outside the message. Report scams.\n\nExplore the official FTC data using the source links in the description.\nREAL-LIFE IQ — Verify first. Act second.",
            "Scammers aren’t just stealing a few dollars anymore. The numbers are getting frighteningly large. According to the latest official FTC data, consumers submitted 3 million fraud reports in 2025 and reported losing 15.9 billion dollars. The biggest money-loss category was investment scams, with 7.9 billion dollars reported lost. The most reported scam category was imposter scams — more than 1 million reports and over 3.5 billion dollars in reported losses. And social media is becoming a major doorway for fraud. The FTC says 2.1 billion dollars was reported lost to scams that started on social media. Nearly 30 percent of people who reported losing money said the scam began there. That’s about eight times the reported social-media scam losses from 2020. And remember: these are only reported losses. The real damage may be even higher. So before you send money, share information, or click that urgent message — stop. Pause before paying. Verify outside the message. And report scams at ReportFraud dot FTC dot gov. For more information, visit ftc dot gov slash scams and ftc dot gov slash exploredata. REAL-LIFE IQ — Verify first. Act second.",
            "Consumers need a concise, trustworthy view of the latest official FTC fraud figures and the biggest current risk categories.",
            "Pause before paying, verify outside the message, and report scams to the FTC.",
            "Published 09-08-2026. FTC Scam Watch #10. Final video 1080x1920, 75.37 seconds, 30 FPS, H.264 + AAC. Full six-slide video and uploaded MP3 validated.",
            now,
            v10["id"],
        ),
    )

    v11 = con.execute("SELECT id FROM videos WHERE number=11").fetchone()
    con.execute(
        """UPDATE videos SET description=?, hashtags=?, youtube_tags=?,
           pinned_comment=?, problem=?, takeaway=?, notes=?, updated_at=?
           WHERE id=?""",
        (
            "A WhatsApp investment group can look convincing. Dozens of members may appear to post profits, withdrawals, and success stories. But stop and ask: who are these people? Scammers can create fake profiles, fake testimonials, fake profit screenshots, and fake withdrawal stories to create social proof and pressure you to invest.\n\nBefore sending money or crypto:\n✅ Verify the investment independently\n✅ Check who actually runs the group\n✅ Ask the group admin direct questions\n✅ Verify the advisor's identity and credentials\n✅ Be suspicious of guaranteed or unusually consistent returns\n✅ Never send money simply because strangers claim they are winning\n\nDon’t trust the crowd. Verify the authenticity outside the WhatsApp group. Ask the right questions. Protect your hard-earned money.\n\nREAL-LIFE IQ — Verify first. Act second.",
            "#WhatsAppScam #InvestmentScam #CryptoScam #InvestmentFraud #ScamAwareness #FraudPrevention #OnlineSafety #WhatsApp #RealLifeIQ #Shorts",
            "WhatsApp investment scam, WhatsApp investment group, WhatsApp scam, investment scam, fake investment group, fake investment profits, fake testimonials, investment fraud, crypto scam, social proof scam, fake trading group, WhatsApp trading scam, guaranteed returns scam, scam awareness, fraud prevention, online safety, Real Life IQ",
            "A group full of “winners” does NOT prove the investment is real.\n\nFake profiles, fake withdrawals, and fake success stories can all be used to build trust.\n\nBefore investing: Verify the people. Verify the investment. Ask questions. Never send money because strangers say they won.\n\nREAL-LIFE IQ — Verify first. Act second.",
            "A WhatsApp investment group can manufacture social proof using fake members, fake testimonials, fake withdrawals, and pressure tactics to make an investment appear legitimate.",
            "Do not trust the crowd. Verify the investment and the people independently outside the WhatsApp group, ask the group admin direct questions, and never invest hard-earned money because strangers claim they won.",
            "Published 09-08-2026. #11 WhatsApp Investment Group social-proof scam. Final video 1080x1920, 56.42 seconds, 30 FPS, H.264 + AAC. All 6 slides validated. Final audio closely matched uploaded MP3 with waveform correlation about 0.99995.",
            now,
            v11["id"],
        ),
    )

    con.commit()
    con.close()
