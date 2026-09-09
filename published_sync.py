from __future__ import annotations

from datetime import datetime


def sync_published() -> None:
    """Idempotently sync published production records added after studio_sync.py."""
    from app import db_connect, ensure_stages

    con = db_connect()
    now = datetime.now().isoformat(timespec="seconds")

    # Keep living schema compatible with the production detail fields.
    columns = {row["name"] for row in con.execute("PRAGMA table_info(videos)").fetchall()}
    if "youtube_tags" not in columns:
        con.execute("ALTER TABLE videos ADD COLUMN youtube_tags TEXT")
    if "voice_over_text" not in columns:
        con.execute("ALTER TABLE videos ADD COLUMN voice_over_text TEXT")

    number = 13
    topic = "Gmail Hacked — Recover, Reclaim & Restore"
    title = "Gmail Hacked? Changing Your Password Is NOT Enough #Shorts"
    published_date = "09-09-2026"

    video = con.execute("SELECT * FROM videos WHERE number=?", (number,)).fetchone()
    if video is None:
        cur = con.execute(
            "INSERT INTO videos(number,topic,status,created_at,updated_at) VALUES(?,?,?,?,?)",
            (number, topic, "Planning", now, now),
        )
        ensure_stages(con, cur.lastrowid)
        video_id = cur.lastrowid
    else:
        video_id = video["id"]
        ensure_stages(con, video_id)

    description = """Someone got into your Gmail or Google Account?

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
Verify first. Act second."""

    hashtags = "#GmailHacked #GoogleAccount #AccountRecovery #GmailSecurity #GoogleSecurity #HackedAccount #CyberSecurity #ScamAwareness #OnlineSafety #RealLifeIQ #Shorts"
    youtube_tags = "Gmail hacked, Gmail account hacked, Google account hacked, Gmail recovery, Google account recovery, recover Gmail account, hacked email account, Gmail security, Google security, account takeover, Gmail forwarding hack, Gmail filters hack, unknown Google devices, Google 2 step verification, recovery email, recovery phone, cyber security, online safety, Real Life IQ"

    pinned_comment = """Changing your password may not finish the cleanup.

After a Gmail or Google Account compromise, also check:
• Unknown signed-in devices
• Recovery phone + recovery email
• Gmail forwarding
• Gmail filters
• Third-party app access
• 2-Step Verification

If you’re locked out, use Google’s official Account Recovery process only.

The official Google links are in the description.

REAL-LIFE IQ — Recover access. Remove hidden changes. Rebuild security."""

    voice_over_text = """Your Gmail may be hacked even if you can still sign in. A hacker may change recovery information, stay signed in on another device, forward your email, or create filters that hide messages. Changing your password alone may not be enough.

If you can still sign in, open your Google Account Security page. Review recent security activity, check your devices, and sign out of anything you don’t recognize.

If you can’t sign in, use Google’s official Account Recovery page. Try from a device and location you’ve used before, answer the recovery questions carefully, and use a recent password if asked. Never pay someone who claims they can recover the account for you.

Once you’re back in, change your Google password, verify your recovery phone and recovery email, and turn on 2-Step Verification.

Then check Gmail itself. Open Settings and inspect Forwarding and POP or IMAP, plus Filters and Blocked Addresses. Remove any forwarding address or filter you didn’t create.

Next, review third-party app access and remove connections you don’t trust. Check Drive, Photos, and YouTube for unexpected changes. If you reused the same password elsewhere, change it there too. If you suspect malware, scan the device.

Remember the rule: recover access, remove hidden changes, and rebuild security. REAL-LIFE IQ — Verify first. Act second."""

    problem = "A compromised Gmail or Google Account may remain unsafe after a password change because an attacker can retain sessions, alter recovery information, add forwarding or filters, or leave third-party access behind."
    takeaway = "Recover access through Google’s official path, remove unknown devices and hidden Gmail changes, verify recovery methods, revoke untrusted app access, and enable 2-Step Verification."
    notes = (
        "Published 09-09-2026. #13 Recover • Reclaim • Restore — Gmail Hacked. "
        "Technically grounded in Google Account Help and Gmail Help. Final approved video uses 7 independent 9:16 slides, "
        "1080x1920 vertical, approximately 82.03 seconds, 30 FPS. Full decode validation passed; no overlapping slides; "
        "embedded audio matched the uploaded MP3 at approximately 0.99995 waveform correlation."
    )

    con.execute(
        """UPDATE videos
           SET topic=?, title=?, description=?, hashtags=?, youtube_tags=?, status='Published',
               problem=?, takeaway=?, upload_date=?, publish_date=?, pinned_comment=?,
               voice_over_text=?, notes=?, updated_at=?
           WHERE id=?""",
        (
            topic, title, description, hashtags, youtube_tags, problem, takeaway,
            published_date, published_date, pinned_comment, voice_over_text, notes, now, video_id,
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

    # P062 is the matching recovery-backlog idea: Gmail Hacked / Google Account Recovery.
    table_names = {row["name"] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    if "ideas" in table_names:
        con.execute("UPDATE ideas SET status='Published' WHERE idea_id='P062'")

    con.commit()
    con.close()
    print("Published sync complete: video #13 Gmail Hacked marked Published; P062 marked Published.")


if __name__ == "__main__":
    sync_published()
