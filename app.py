from __future__ import annotations

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from security import install_auth
from studio_sync import sync_whatsapp_series

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data"))).resolve()
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "studio.db"
SEED_DIR = BASE_DIR / "seed"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "mp3", "wav", "mp4", "mov", "pptx", "pdf", "xlsx", "txt", "docx"}

PIPELINE = [
    ("problem", "Problem Definition"),
    ("slides", "Slides Verification"),
    ("voice", "Voice-over Verification"),
    ("final_video", "Final Video"),
    ("publishing", "Title / Description / Hashtags"),
    ("published", "Published"),
    ("metrics", "Metrics"),
]

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="REAL-LIFE IQ Content Studio")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
install_auth(app, templates)


def db_connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def ensure_stages(con, video_id: int, approved_through: Optional[str] = None):
    order_map = {k: i + 1 for i, (k, _) in enumerate(PIPELINE)}
    approved_order = order_map.get(approved_through, 0) if approved_through else 0
    for i, (key, name) in enumerate(PIPELINE, start=1):
        status = "Approved" if i <= approved_order else "Not Started"
        approved_at = datetime.now().isoformat(timespec="seconds") if status == "Approved" else None
        con.execute(
            "INSERT OR IGNORE INTO stages(video_id,stage_key,stage_name,order_no,status,approved_at) VALUES(?,?,?,?,?,?)",
            (video_id, key, name, i, status, approved_at),
        )


def init_db():
    con = db_connect()
    con.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number INTEGER UNIQUE NOT NULL,
            topic TEXT NOT NULL,
            title TEXT, description TEXT, hashtags TEXT,
            status TEXT NOT NULL DEFAULT 'Planning',
            problem TEXT, takeaway TEXT,
            upload_date TEXT, publish_date TEXT, youtube_url TEXT,
            pinned_comment TEXT, notes TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            stage_key TEXT NOT NULL, stage_name TEXT NOT NULL,
            order_no INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'Not Started',
            approved_at TEXT, notes TEXT,
            UNIQUE(video_id, stage_key),
            FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL, asset_type TEXT NOT NULL,
            original_name TEXT NOT NULL, stored_name TEXT NOT NULL,
            relative_path TEXT NOT NULL, created_at TEXT NOT NULL,
            FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE
        );
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
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL, captured_at TEXT NOT NULL,
            views INTEGER DEFAULT 0, likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0, subscribers INTEGER DEFAULT 0,
            avg_view_duration REAL, avg_percent_viewed REAL,
            viewed_vs_swiped REAL, notes TEXT,
            FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE
        );
        """
    )
    con.commit(); con.close()
    seed_if_empty()


def seed_if_empty():
    con = db_connect()
    now = datetime.now().isoformat(timespec="seconds")
    if con.execute("SELECT COUNT(*) c FROM videos").fetchone()["c"] == 0:
        seeds = [
            (1,"Bank Scam","Your Bank Says an $846 Purchase Is Pending. What Do You Do?","Published",
             "Recognize a fake bank purchase alert and verify it without using the inbound message.",
             "Verify outside the message using the bank's official app or website.","2026-09-06","2026-09-06","published",
             "You receive a text saying your bank has an $846 purchase pending. Do not use the inbound link or number. Open your bank's official app or website yourself and verify the account.\n\nREAL-LIFE IQ — Smarter Choices for Real Life.",
             "#ScamAwareness #OnlineSafety #RealLifeIQ #Shorts"),
            (2,"Fake Toll Text","Fake Toll Payment Text Scam: Don't Click That Link! #Shorts","Published",
             "Recognize a fake unpaid-toll text before clicking a payment link or entering card information.",
             "Never pay from an unexpected toll text; verify on the official toll agency site or app.","2026-09-06","2026-09-06","published",
             "Did you receive a text saying you have an unpaid toll? Verify through the official toll agency website or app instead of the text link.\n\nREAL-LIFE IQ — Smarter Choices for Real Life.",
             "#TollScam #FakeTollText #TextScam #ScamAwareness #RealLifeIQ #Shorts"),
            (3,"Package Delivery Scam","Package Delivery Scam Alert: Don't Click That Text Link! #Shorts","Final Ready",
             "Recognize fake package-delivery texts that use address problems or small redelivery fees to lure people into clicking.",
             "Do not use the message link; verify the shipment independently on the carrier's official site or app.",None,None,"final_video",
             "Got a text saying your package can't be delivered or that you need to pay a small redelivery fee? Check the package directly through the official carrier website or app. Block, report, and delete suspicious messages.\n\nREAL-LIFE IQ — Smarter Choices for Real Life.",
             "#PackageScam #DeliveryScam #TextScam #ScamAwareness #OnlineSafety #Smishing #RealLifeIQ #Shorts"),
            (4,"WhatsApp Verification Code Scam","","Problem Definition",
             "A scammer uses a trusted-looking WhatsApp message to persuade someone to share a six-digit verification code, which can help the scammer take over the account. The viewer should learn that verification codes are private and must never be shared — even with a friend who appears to ask for one.",
             "Never share a verification code. If a friend asks for one, contact them through another known method before doing anything.",None,None,None,"","")
        ]
        for number,topic,title,status,problem,takeaway,upload,publish,approved,description,hashtags in seeds:
            cur = con.execute(
                "INSERT INTO videos(number,topic,title,status,problem,takeaway,upload_date,publish_date,description,hashtags,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (number,topic,title,status,problem,takeaway,upload,publish,description,hashtags,now,now)
            )
            ensure_stages(con, cur.lastrowid, approved)
            if number == 4:
                con.execute("UPDATE stages SET status='In Review' WHERE video_id=? AND stage_key='problem'", (cur.lastrowid,))

    if con.execute("SELECT COUNT(*) c FROM assets").fetchone()["c"] == 0:
        bundled = {
            1: "REAL_LIFE_IQ_Bank_Scam_FixedFrames_ExactVoice_FINAL.mp4",
            2: "REAL_LIFE_IQ_Fake_Toll_Girl_SoftVoice.mp4",
            3: "package_delivery_scam_FINAL_with_voiceover.mp4",
        }
        for number, fname in bundled.items():
            v = con.execute("SELECT id FROM videos WHERE number=?", (number,)).fetchone()
            if v:
                path = UPLOAD_DIR / str(v["id"]) / fname
                if path.exists():
                    con.execute("INSERT INTO assets(video_id,asset_type,original_name,stored_name,relative_path,created_at) VALUES(?,?,?,?,?,?)",
                                (v["id"],"Final Video",fname,fname,str(path.relative_to(DATA_DIR)),now))

    catalog = SEED_DIR / "catalog.json"
    if catalog.exists():
        try:
            seed = json.loads(catalog.read_text(encoding="utf-8"))
            if con.execute("SELECT COUNT(*) c FROM ideas").fetchone()["c"] == 0:
                for row in seed.get("ideas", []):
                    con.execute(
                        """INSERT OR IGNORE INTO ideas(idea_id,pillar,series,working_title,hook,problem,safe_action,audience,priority,score,status,source_name,source_url,notes,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (row.get("idea_id"), row.get("pillar"), row.get("series"), row.get("working_title"),
                         row.get("hook"), row.get("problem"), row.get("safe_action"), row.get("audience"),
                         row.get("priority"), row.get("score"), row.get("status"), row.get("source_name"),
                         row.get("source_url"), row.get("notes"), now),
                    )
            if con.execute("SELECT COUNT(*) c FROM sources").fetchone()["c"] == 0:
                for row in seed.get("sources", []):
                    con.execute(
                        "INSERT OR IGNORE INTO sources(name,authority,best_for,url,editorial_note) VALUES(?,?,?,?,?)",
                        (row.get("name"), row.get("authority"), row.get("best_for"), row.get("url"), row.get("editorial_note")),
                    )
        except Exception as exc:
            print("Seed catalog import skipped:", exc)
    con.commit(); con.close()


def current_stage(stages):
    for s in stages:
        if s["status"] != "Approved": return s["stage_name"]
    return "Complete"


def ctx(request: Request, **kwargs):
    return {"request": request, "pipeline": PIPELINE, "now_year": datetime.now().year, **kwargs}


@app.get("/", response_class=HTMLResponse, name="dashboard")
def dashboard(request: Request):
    con = db_connect(); videos = con.execute("SELECT * FROM videos ORDER BY number").fetchall()
    stages_map={v["id"]:con.execute("SELECT * FROM stages WHERE video_id=? ORDER BY order_no",(v["id"],)).fetchall() for v in videos}
    published=sum(1 for v in videos if v["status"]=="Published"); ready=sum(1 for v in videos if "Ready" in (v["status"] or ""))
    ideas_count=con.execute("SELECT COUNT(*) c FROM ideas").fetchone()["c"]
    next_video=next((v for v in videos if v["status"]!="Published"),None)
    metric=con.execute("SELECT COALESCE(SUM(views),0) views,COALESCE(SUM(likes),0) likes,COALESCE(SUM(comments),0) comments FROM metrics WHERE id IN (SELECT MAX(id) FROM metrics GROUP BY video_id)").fetchone()
    con.close(); return templates.TemplateResponse(request, "dashboard.html", ctx(request,videos=videos,stages_map=stages_map,published=published,ready=ready,ideas_count=ideas_count,next_video=next_video,metric=metric,current_stage=current_stage))


@app.get("/videos", response_class=HTMLResponse, name="videos")
def videos_page(request: Request):
    con=db_connect(); rows=con.execute("SELECT * FROM videos ORDER BY number").fetchall(); stage_info={v["id"]:current_stage(con.execute("SELECT * FROM stages WHERE video_id=? ORDER BY order_no",(v["id"],)).fetchall()) for v in rows}; con.close()
    return templates.TemplateResponse(request,"videos.html",ctx(request,videos=rows,stage_info=stage_info))


@app.post("/videos/new", name="new_video")
def new_video(topic: str = Form(...)):
    topic=topic.strip(); con=db_connect(); number=con.execute("SELECT COALESCE(MAX(number),0)+1 n FROM videos").fetchone()["n"]; now=datetime.now().isoformat(timespec="seconds")
    cur=con.execute("INSERT INTO videos(number,topic,status,created_at,updated_at) VALUES(?,?,?,?,?)",(number,topic,"Planning",now,now)); ensure_stages(con,cur.lastrowid); con.commit(); vid=cur.lastrowid; con.close()
    return RedirectResponse(url=f"/videos/{vid}",status_code=303)


@app.get("/videos/{video_id}", response_class=HTMLResponse, name="video_detail")
def video_detail(request: Request, video_id: int):
    con=db_connect(); video=con.execute("SELECT * FROM videos WHERE id=?",(video_id,)).fetchone()
    if not video: con.close(); raise HTTPException(404)
    stages=con.execute("SELECT * FROM stages WHERE video_id=? ORDER BY order_no",(video_id,)).fetchall(); assets=con.execute("SELECT * FROM assets WHERE video_id=? ORDER BY created_at DESC",(video_id,)).fetchall(); metrics=con.execute("SELECT * FROM metrics WHERE video_id=? ORDER BY captured_at DESC",(video_id,)).fetchall(); con.close()
    return templates.TemplateResponse(request,"video_detail.html",ctx(request,video=video,stages=stages,assets=assets,metrics=metrics))


@app.post("/videos/{video_id}/update", name="update_video")
def update_video(video_id:int, topic:str=Form(""), title:str=Form(""), description:str=Form(""), hashtags:str=Form(""), status:str=Form("Planning"), problem:str=Form(""), takeaway:str=Form(""), upload_date:str=Form(""), publish_date:str=Form(""), youtube_url:str=Form(""), pinned_comment:str=Form(""), notes:str=Form("")):
    fields=[topic,title,description,hashtags,status,problem,takeaway,upload_date,publish_date,youtube_url,pinned_comment,notes]; vals=[x.strip() or None for x in fields]; now=datetime.now().isoformat(timespec="seconds")
    con=db_connect(); con.execute("UPDATE videos SET topic=?,title=?,description=?,hashtags=?,status=?,problem=?,takeaway=?,upload_date=?,publish_date=?,youtube_url=?,pinned_comment=?,notes=?,updated_at=? WHERE id=?",(*vals,now,video_id)); con.commit(); con.close(); return RedirectResponse(url=f"/videos/{video_id}",status_code=303)


@app.post("/videos/{video_id}/stages/{stage_key}", name="update_stage")
def update_stage(video_id:int, stage_key:str, action:str=Form(...), notes:str=Form("")):
    con=db_connect(); stage=con.execute("SELECT * FROM stages WHERE video_id=? AND stage_key=?",(video_id,stage_key)).fetchone()
    if not stage: con.close(); raise HTTPException(404)
    notes=notes.strip() or None
    if action=="approve":
        con.execute("UPDATE stages SET status='Approved',approved_at=?,notes=COALESCE(?,notes) WHERE id=?",(datetime.now().isoformat(timespec="seconds"),notes,stage["id"])); nxt=con.execute("SELECT * FROM stages WHERE video_id=? AND order_no=?",(video_id,stage["order_no"]+1)).fetchone()
        if nxt and nxt["status"]=="Not Started": con.execute("UPDATE stages SET status='In Review' WHERE id=?",(nxt["id"],))
    elif action in {"review","reopen"}: con.execute("UPDATE stages SET status='In Review',approved_at=NULL,notes=COALESCE(?,notes) WHERE id=?",(notes,stage["id"]))
    elif action=="not_started": con.execute("UPDATE stages SET status='Not Started',approved_at=NULL,notes=COALESCE(?,notes) WHERE id=?",(notes,stage["id"]))
    con.commit(); con.close(); return RedirectResponse(url=f"/videos/{video_id}",status_code=303)


@app.post("/videos/{video_id}/assets", name="upload_asset")
async def upload_asset(video_id:int, asset_type:str=Form("Other"), file:UploadFile=File(...)):
    original=file.filename or "upload"; ext=original.rsplit(".",1)[-1].lower() if "." in original else ""
    if ext not in ALLOWED_EXTENSIONS: raise HTTPException(400,"File type not allowed")
    safe="".join(c if c.isalnum() or c in "._-" else "_" for c in original); stamp=datetime.now().strftime("%Y%m%d_%H%M%S_%f"); stored=f"{stamp}_{safe}"; folder=UPLOAD_DIR/str(video_id); folder.mkdir(parents=True,exist_ok=True); path=folder/stored
    with path.open("wb") as f:
        while chunk:=await file.read(1024*1024): f.write(chunk)
    con=db_connect(); con.execute("INSERT INTO assets(video_id,asset_type,original_name,stored_name,relative_path,created_at) VALUES(?,?,?,?,?,?)",(video_id,asset_type,original,stored,str(path.relative_to(DATA_DIR)),datetime.now().isoformat(timespec="seconds"))); con.commit(); con.close(); return RedirectResponse(url=f"/videos/{video_id}",status_code=303)


@app.get("/assets/{asset_id}", name="download_asset")
def download_asset(asset_id:int):
    con=db_connect(); a=con.execute("SELECT * FROM assets WHERE id=?",(asset_id,)).fetchone(); con.close()
    if not a: raise HTTPException(404)
    path=DATA_DIR/a["relative_path"]
    return FileResponse(path,filename=a["original_name"])


@app.post("/videos/{video_id}/metrics", name="add_metrics")
def add_metrics(video_id:int, captured_at:str=Form(""), views:str=Form(""), likes:str=Form(""), comments:str=Form(""), subscribers:str=Form(""), avg_percent_viewed:str=Form(""), viewed_vs_swiped:str=Form(""), notes:str=Form("")):
    def integer(x): return int(x) if x.strip() else 0
    def decimal(x): return float(x) if x.strip() else None
    con=db_connect(); con.execute("INSERT INTO metrics(video_id,captured_at,views,likes,comments,subscribers,avg_percent_viewed,viewed_vs_swiped,notes) VALUES(?,?,?,?,?,?,?,?,?)",(video_id,captured_at or datetime.now().date().isoformat(),integer(views),integer(likes),integer(comments),integer(subscribers),decimal(avg_percent_viewed),decimal(viewed_vs_swiped),notes or None)); con.commit(); con.close(); return RedirectResponse(url=f"/videos/{video_id}",status_code=303)


@app.get("/ideas", response_class=HTMLResponse, name="ideas")
def ideas_page(request:Request,q:str="",status:str="",pillar:str=""):
    con=db_connect(); sql="SELECT * FROM ideas WHERE 1=1"; args=[]
    if q: sql+=" AND (working_title LIKE ? OR problem LIKE ? OR hook LIKE ?)"; args += [f"%{q}%"]*3
    if status: sql+=" AND status=?"; args.append(status)
    if pillar: sql+=" AND pillar=?"; args.append(pillar)
    sql+=" ORDER BY CASE WHEN priority LIKE 'A+%' THEN 1 WHEN priority LIKE 'A /%' THEN 2 ELSE 3 END,score DESC,idea_id"; rows=con.execute(sql,args).fetchall(); pillars=[r[0] for r in con.execute("SELECT DISTINCT pillar FROM ideas WHERE pillar IS NOT NULL ORDER BY pillar")]; statuses=[r[0] for r in con.execute("SELECT DISTINCT status FROM ideas WHERE status IS NOT NULL ORDER BY status")]; con.close()
    return templates.TemplateResponse(request,"ideas.html",ctx(request,ideas=rows,pillars=pillars,statuses=statuses,q=q,status=status,pillar=pillar))


@app.post("/ideas/{idea_id}/promote", name="promote_idea")
def promote_idea(idea_id:int):
    con=db_connect(); idea=con.execute("SELECT * FROM ideas WHERE id=?",(idea_id,)).fetchone()
    if not idea: con.close(); raise HTTPException(404)
    number=con.execute("SELECT COALESCE(MAX(number),0)+1 n FROM videos").fetchone()["n"]; now=datetime.now().isoformat(timespec="seconds"); cur=con.execute("INSERT INTO videos(number,topic,title,status,problem,takeaway,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",(number,idea["working_title"],idea["working_title"],"Problem Definition",idea["problem"],idea["safe_action"],f"Created from idea {idea['idea_id'] or idea['id']}",now,now)); ensure_stages(con,cur.lastrowid); con.execute("UPDATE stages SET status='In Review' WHERE video_id=? AND stage_key='problem'",(cur.lastrowid,)); con.execute("UPDATE ideas SET status='In Production' WHERE id=?",(idea_id,)); con.commit(); vid=cur.lastrowid; con.close(); return RedirectResponse(url=f"/videos/{vid}",status_code=303)


@app.get("/sources", response_class=HTMLResponse, name="sources")
def sources_page(request:Request):
    con=db_connect(); rows=con.execute("SELECT * FROM sources ORDER BY authority,name").fetchall(); con.close(); return templates.TemplateResponse(request,"sources.html",ctx(request,sources=rows))


@app.get("/health", name="health")
def health(): return JSONResponse({"status":"ok","app":"REAL-LIFE IQ Content Studio"})


init_db()
sync_whatsapp_series(db_connect, ensure_stages)
