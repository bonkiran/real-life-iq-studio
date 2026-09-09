from __future__ import annotations

from datetime import datetime


def sync_published() -> None:
    """Idempotently sync published production records added after studio_sync.py."""
    from app import db_connect, ensure_stages

    con = db_connect()
    now = datetime.now().isoformat(timespec="seconds")

    columns = {row["name"] for row in con.execute("PRAGMA table_info(videos)").fetchall()}
    if "youtube_tags" not in columns:
        con.execute("ALTER TABLE videos ADD COLUMN youtube_tags TEXT")
    if "voice_over_text" not in columns:
        con.execute("ALTER TABLE videos ADD COLUMN voice_over_text TEXT")

    records = [
        {
            "number": 13,
            "topic": "Gmail Hacked — Recover, Reclaim & Restore",
            "title": "Gmail Hacked? Changing Your Password Is NOT Enough #Shorts",
            "published_date": "09-09-2026",
            "description": """Someone got into your Gmail or Google Account?

Changing the password is important — but it may not be the only thing you need to check.

An attacker may have stayed signed in on another device, changed your recovery phone or recovery email, added mail forwarding, created Gmail filters that hide, delete, or forward messages, or connected third-party apps to your Google Account.

If you can still sign in:
• Open Google Account → Security
• Review Recent security activity
• Check Your devices
• Sign out of devices you don’t recognize
• Change your password

If you cannot sign in, use Google’s official Account Recovery process. Try from a device and location you have used with the account before and answer the recovery questions as accurately as possible.

After you recover access:
• Verify your recovery phone and recovery email
• Turn on 2-Step Verification
• Check Gmail Forwarding and POP/IMAP
• Review Filters and Blocked Addresses
• Remove unfamiliar third-party app access
• Check Drive, Photos, YouTube, and other Google services for unexpected changes
• Change the password anywhere else you reused the same password

Never pay a stranger who claims they can recover your Gmail account for you.

Official Google resources:
https://support.google.com/accounts/answer/6294825
https://accounts.google.com/signin/recovery
https://support.google.com/accounts/answer/7682439
https://support.google.com/accounts/answer/183723
https://support.google.com/mail/answer/6579

REAL-LIFE IQ — Recover access. Remove hidden changes. Rebuild security.
Verify first. Act second.""",
            "hashtags": "#GmailHacked #GoogleAccount #AccountRecovery #GmailSecurity #GoogleSecurity #HackedAccount #CyberSecurity #ScamAwareness #OnlineSafety #RealLifeIQ #Shorts",
            "youtube_tags": "Gmail hacked, Gmail account hacked, Google account hacked, Gmail recovery, Google account recovery, recover Gmail account, hacked email account, Gmail security, Google security, account takeover, Gmail forwarding hack, Gmail filters hack, unknown Google devices, Google 2 step verification, recovery email, recovery phone, cyber security, online safety, Real Life IQ",
            "pinned_comment": """Changing your password may not finish the cleanup.

After a Gmail or Google Account compromise, also check:
• Unknown signed-in devices
• Recovery phone + recovery email
• Gmail forwarding
• Gmail filters
• Third-party app access
• 2-Step Verification

If you’re locked out, use Google’s official Account Recovery process only.

The official Google links are in the description.

REAL-LIFE IQ — Recover access. Remove hidden changes. Rebuild security.""",
            "voice_over_text": """Your Gmail may be hacked even if you can still sign in. A hacker may change recovery information, stay signed in on another device, forward your email, or create filters that hide messages. Changing your password alone may not be enough.

If you can still sign in, open your Google Account Security page. Review recent security activity, check your devices, and sign out of anything you don’t recognize.

If you can’t sign in, use Google’s official Account Recovery page. Try from a device and location you’ve used before, answer the recovery questions carefully, and use a recent password if asked. Never pay someone who claims they can recover the account for you.

Once you’re back in, change your Google password, verify your recovery phone and recovery email, and turn on 2-Step Verification.

Then check Gmail itself. Open Settings and inspect Forwarding and POP or IMAP, plus Filters and Blocked Addresses. Remove any forwarding address or filter you didn’t create.

Next, review third-party app access and remove connections you don’t trust. Check Drive, Photos, and YouTube for unexpected changes. If you reused the same password elsewhere, change it there too. If you suspect malware, scan the device.

Remember the rule: recover access, remove hidden changes, and rebuild security. REAL-LIFE IQ — Verify first. Act second.""",
            "problem": "A compromised Gmail or Google Account may remain unsafe after a password change because an attacker can retain sessions, alter recovery information, add forwarding or filters, or leave third-party access behind.",
            "takeaway": "Recover access through Google’s official path, remove unknown devices and hidden Gmail changes, verify recovery methods, revoke untrusted app access, and enable 2-Step Verification.",
            "notes": "Published 09-09-2026. #13 Recover • Reclaim • Restore — Gmail Hacked. Technically grounded in Google Account Help and Gmail Help. Final approved video uses 7 independent 9:16 slides, 1080x1920 vertical, approximately 82.03 seconds, 30 FPS. Full decode validation passed; no overlapping slides; embedded audio matched the uploaded MP3 at approximately 0.99995 waveform correlation.",
            "idea_id": "P062",
        },
        {
            "number": 14,
            "topic": "Bank Account Hacked — Recover, Reclaim & Restore",
            "title": "Bank Account Hacked? What to Do in the First 15 Minutes #Shorts",
            "published_date": "09-09-2026",
            "description": """You open your bank account and see a withdrawal, transfer, or transaction you never made or authorized. What you do next matters.

Act quickly:
• Contact your bank immediately using the official number in the bank app, on the back of your card, or on the bank’s official website.
• Report the unauthorized activity and ask the bank what should be secured, frozen, or replaced.
• Ask whether any pending unauthorized transfers can still be stopped.
• Change your online-banking password from a trusted device.
• Turn on stronger authentication if your bank provides it.
• Review recent transactions, including small amounts you don’t recognize.
• Take screenshots and save transaction IDs, dates, amounts, case numbers, and confirmation numbers.
• Secure the email address and phone number connected to your bank account.
• Review payment apps, debit/credit cards, and other connected financial accounts.
• Continue monitoring the account and follow your bank’s formal fraud/dispute process.

Important: This video covers transactions initiated without your authorization. If you personally sent money because a scammer tricked you, the recovery process can be different; that is covered separately in REAL-LIFE IQ #15.

Official resources:
https://www.consumerfinance.gov/ask-cfpb/how-do-i-get-my-money-back-after-i-discover-an-unauthorized-transaction-or-money-missing-from-my-bank-account-en-1017/
https://www.consumerfinance.gov/compliance/compliance-resources/deposit-accounts-resources/electronic-fund-transfers/electronic-fund-transfers-faqs/
https://www.consumerfinance.gov/consumer-tools/fraud/
https://consumer.ftc.gov/articles/what-do-if-you-were-scammed

REAL-LIFE IQ — Recover. Reclaim. Restore.
Verify first. Act second.""",
            "hashtags": "#BankAccountHacked #BankFraud #UnauthorizedTransaction #AccountTakeover #FraudAlert #FraudPrevention #AccountSecurity #ScamAwareness #CyberSafety #OnlineSafety #RealLifeIQ #Shorts",
            "youtube_tags": "bank account hacked, bank account fraud, hacked bank account, unauthorized transaction, unauthorized bank transfer, money missing from bank account, bank fraud what to do, account takeover, online banking hacked, stolen banking credentials, bank account recovery, debit card fraud, banking security, fraud prevention, secure bank account, CFPB Regulation E, electronic fund transfer fraud, scam awareness, cyber safety, Real Life IQ",
            "pinned_comment": """If money disappeared from your bank account without your authorization, don’t wait.

1. Contact the bank using an official number
2. Report the unauthorized activity
3. Secure your login
4. Review every transaction
5. Document everything
6. Secure your email + phone
7. Monitor the account and follow the bank’s dispute process

Different situation: If you sent the money yourself because a scammer tricked you, that requires a different recovery path. That’s coming in #15.

Official CFPB and FTC resources are linked in the description.

REAL-LIFE IQ — Recover. Reclaim. Restore.""",
            "voice_over_text": """You open your bank app and see money gone — a withdrawal or transfer you never made. That sinking feeling is real. But don’t freeze. What you do in the next few minutes can make a difference.

Call your bank immediately using the official number in your bank app, on the back of your card, or on the bank’s official website. Report the unauthorized transaction. Ask them to secure the account, freeze cards if needed, and check whether any pending transfers can still be stopped.

Next, change your online banking password from a trusted device. Use a strong, unique password and turn on two-step verification if your bank offers it. Never reuse that password anywhere else.

Now look closely at recent activity. Don’t ignore small charges. A few dollars you don’t recognize can still be a warning sign.

Take screenshots and write everything down — dates, amounts, transaction IDs, confirmation numbers, and the bank’s case number. Keep a record of who you spoke with and when.

Then protect what connects to your bank: your email, phone number, payment apps, debit cards, and credit cards. Change reused passwords. If your email or phone is compromised, the attacker may still have another way back in.

Money disappearing from your account can feel frightening and personal. But you still have actions you can take. Contact the bank fast, secure your access, document everything, monitor your account, and follow the bank’s dispute process. Act fast. Stay alert. REAL-LIFE IQ — Verify first. Act second.""",
            "problem": "A viewer discovers an unauthorized withdrawal, transfer, login, or other bank-account activity and needs a fast, technically grounded recovery sequence before more money or account access is lost.",
            "takeaway": "Contact the bank through an official channel immediately, report unauthorized activity, secure online-banking credentials, review and document transactions, protect connected email and phone accounts, and follow the bank’s formal dispute process.",
            "notes": "Published 09-09-2026. #14 Recover • Reclaim • Restore — Bank Account Hacked. Core recovery guidance is grounded in CFPB Regulation E / unauthorized electronic transfer guidance and FTC scam recovery resources. Final corrected video uses 7 independent 9:16 slides, 1080x1920 vertical, 92.4 seconds, 30 FPS. Slide 7 was rebuilt cleanly after QA; final version has no neighboring-slide bleed or overlap and was rechecked at narration transition boundaries.",
            "idea_id": "P063",
        },
    ]

    for record in records:
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
                   problem=?, takeaway=?, upload_date=?, publish_date=?, pinned_comment=?,
                   voice_over_text=?, notes=?, updated_at=?
               WHERE id=?""",
            (
                record["topic"], record["title"], record["description"], record["hashtags"],
                record["youtube_tags"], record["problem"], record["takeaway"],
                record["published_date"], record["published_date"], record["pinned_comment"],
                record["voice_over_text"], record["notes"], now, video_id,
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

        table_names = {row["name"] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "ideas" in table_names:
            con.execute("UPDATE ideas SET status='Published' WHERE idea_id=?", (record["idea_id"],))

    con.commit()
    con.close()
    print("Published sync complete: videos #13 and #14 marked Published; P062 and P063 marked Published.")


if __name__ == "__main__":
    sync_published()
