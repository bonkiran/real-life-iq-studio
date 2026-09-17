from __future__ import annotations

from datetime import datetime


def sync_latest_status() -> None:
    """Preserve confirmed publication state without overriding the channel snapshot.

    The canonical REAL-LIFE IQ publication list now comes from
    seed/published_videos.json via studio_sync.sync_whatsapp_series().
    This module only protects a couple of historically hand-maintained records from
    being downgraded by older databases. It must never put a confirmed published
    video back into HOLD or In Review.
    """
    from app import db_connect, ensure_stages

    con = db_connect()
    now = datetime.now().isoformat(timespec="seconds")

    # These two records previously had one-off logic in this file. Both are now
    # confirmed published on YouTube and must remain Published.
    for number in (22, 23):
        video = con.execute("SELECT * FROM videos WHERE number=?", (number,)).fetchone()
        if not video:
            continue

        ensure_stages(con, video["id"])
        con.execute(
            "UPDATE videos SET status='Published', updated_at=? WHERE id=?",
            (now, video["id"]),
        )

        # Work with either the original seven-stage schema or the newer six-phase
        # production schema without inventing stages that are not present.
        for stage in con.execute(
            "SELECT * FROM stages WHERE video_id=? ORDER BY order_no",
            (video["id"],),
        ).fetchall():
            con.execute(
                "UPDATE stages SET status='Approved', approved_at=COALESCE(approved_at, ?) WHERE id=?",
                (now, stage["id"]),
            )

    con.commit()
    con.close()
    print("Latest status sync complete: confirmed published records remain Published; no HOLD overrides applied.")


if __name__ == "__main__":
    sync_latest_status()
