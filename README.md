# REAL-LIFE IQ Content Studio

A lightweight web app for managing the REAL-LIFE IQ video creation workflow in one place.

## V1 features

- Dashboard for production status
- One workspace per video
- Approval gates: Problem → Slides → Voice-over → Final Video → Publishing Package → Published → Metrics
- Asset uploads for images, slides, audio, video and research files
- 60-idea strategic backlog preloaded
- 16 trusted research sources preloaded
- Videos #1–#4 preloaded as project records
- Manual metrics snapshots now; YouTube integration later

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app:app --reload --port 5000
```

Open http://127.0.0.1:5000

## Data and persistence

By default the app stores SQLite data and uploaded assets under `./data`. You can set `DATA_DIR` to another directory.

Render's default filesystem is ephemeral. For a real ongoing production workspace, point `DATA_DIR` at a persistent disk or move the database/assets to managed storage.

The public source repository intentionally does **not** contain the finished MP4 files. Upload production assets through the app once persistent storage is enabled.

## Render deployment

`render.yaml` is included. V1 can be deployed as a Python web service for testing. Before relying on it as the permanent asset store, enable persistent storage.

## Planned next versions

- AI-assisted slide/image generation
- Voice-over generation inside a workspace
- Automatic final-video assembly
- YouTube Data/Analytics API connection
- Thumbnail and pinned-comment workflow
- Version history and richer approvals
- Cloud object storage
