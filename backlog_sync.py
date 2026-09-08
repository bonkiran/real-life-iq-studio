from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data"))).resolve()
DB_PATH = DATA_DIR / "studio.db"
SEED_FILES = [
    BASE_DIR / "seed" / "catalog.json",
    BASE_DIR / "seed" / "recovery_backlog.json",
]


def sync_backlog() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().isoformat(timespec="seconds")

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idea_id TEXT UNIQUE, pillar TEXT, series TEXT,
            working_title TEXT NOT NULL, hook TEXT, problem TEXT,
            safe_action TEXT, audience TEXT, priority TEXT, score REAL,
            status TEXT DEFAULT 'Backlog', source_name TEXT, source_url TEXT,
            notes TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL, authority TEXT, best_for TEXT,
            url TEXT, editorial_note TEXT
        );
        """
    )

    ideas_added = 0
    sources_added = 0
    files_loaded = 0

    for seed_file in SEED_FILES:
        if not seed_file.exists():
            print(f"Backlog seed skipped: {seed_file} not found")
            continue

        payload = json.loads(seed_file.read_text(encoding="utf-8"))
        files_loaded += 1

        for row in payload.get("ideas", []):
            before = con.total_changes
            con.execute(
                """INSERT OR IGNORE INTO ideas(
                       idea_id,pillar,series,working_title,hook,problem,safe_action,
                       audience,priority,score,status,source_name,source_url,notes,created_at
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    row.get("idea_id"), row.get("pillar"), row.get("series"),
                    row.get("working_title"), row.get("hook"), row.get("problem"),
                    row.get("safe_action"), row.get("audience"), row.get("priority"),
                    row.get("score"), row.get("status", "Backlog"), row.get("source_name"),
                    row.get("source_url"), row.get("notes"), now,
                ),
            )
            if con.total_changes > before:
                ideas_added += 1

        for row in payload.get("sources", []):
            before = con.total_changes
            con.execute(
                "INSERT OR IGNORE INTO sources(name,authority,best_for,url,editorial_note) VALUES(?,?,?,?,?)",
                (
                    row.get("name"), row.get("authority"), row.get("best_for"),
                    row.get("url"), row.get("editorial_note"),
                ),
            )
            if con.total_changes > before:
                sources_added += 1

    con.commit()
    total_ideas = con.execute("SELECT COUNT(*) FROM ideas").fetchone()[0]
    total_sources = con.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    con.close()

    print(
        f"Backlog sync complete: {files_loaded} seed files, +{ideas_added} ideas, "
        f"+{sources_added} sources (totals: {total_ideas} ideas, {total_sources} sources)."
    )


if __name__ == "__main__":
    sync_backlog()
