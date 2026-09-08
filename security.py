from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from urllib.parse import quote

from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from youtube_metrics import install_youtube_metrics
from youtube_analytics import install_youtube_analytics
from content_hub import install_content_hub

COOKIE_NAME = "rliq_studio_session"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7


def _username() -> str:
    return os.getenv("STUDIO_USERNAME", "admin").strip() or "admin"


def _password() -> str:
    return os.getenv("STUDIO_PASSWORD", "")


def _secret() -> bytes:
    material = f"{_username()}\0{_password()}".encode("utf-8")
    return hashlib.sha256(material).digest()


def _make_token() -> str:
    expiry = int(time.time()) + COOKIE_MAX_AGE
    payload = f"{_username()}|{expiry}"
    signature = hmac.new(_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    raw = f"{payload}|{signature}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _valid_token(token: str | None) -> bool:
    if not token or not _password():
        return False
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        user, expiry_text, signature = raw.rsplit("|", 2)
        if user != _username() or int(expiry_text) < int(time.time()):
            return False
        payload = f"{user}|{expiry_text}"
        expected = hmac.new(_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)
    except Exception:
        return False


def _safe_next(value: str | None) -> str:
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return "/channels"


def _setup_required() -> HTMLResponse:
    return HTMLResponse(
        """
        <!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
        <title>Impact Content Studio — Security Setup</title>
        <style>body{margin:0;background:#0b1f33;color:#e9f2f9;font-family:Inter,system-ui,Segoe UI,Arial,sans-serif;display:grid;place-items:center;min-height:100vh}.box{width:min(560px,90vw);background:#102a43;border:1px solid #28516f;border-radius:18px;padding:32px;box-shadow:0 20px 60px rgba(0,0,0,.3)}h1{margin:0 0 10px;font-size:25px}p{color:#b8cadd;line-height:1.55}code{background:#071726;padding:3px 7px;border-radius:5px;color:#ffd477}</style></head>
        <body><div class='box'><h1>Impact Content Studio</h1><p><strong>Security setup required.</strong></p><p>The Studio is locked until a Render environment variable named <code>STUDIO_PASSWORD</code> is set. Optional username: <code>STUDIO_USERNAME</code> (defaults to <code>admin</code>).</p><p>After saving the variable in Render, redeploy or restart the service and return here.</p></div></body></html>
        """,
        status_code=503,
    )


def install_auth(app, templates) -> None:
    @app.middleware("http")
    async def studio_auth(request: Request, call_next):
        path = request.url.path
        if path == "/health" or path.startswith("/static/") or path in {"/login", "/logout", "/youtube/oauth/callback"}:
            return await call_next(request)
        if not _password():
            return _setup_required()
        if not _valid_token(request.cookies.get(COOKIE_NAME)):
            destination = quote(path + (("?" + request.url.query) if request.url.query else ""), safe="/?=&")
            return RedirectResponse(url=f"/login?next={destination}", status_code=303)
        return await call_next(request)

    @app.get("/login", response_class=HTMLResponse, name="login")
    def login_page(request: Request, next: str = "/channels"):
        if not _password():
            return _setup_required()
        if _valid_token(request.cookies.get(COOKIE_NAME)):
            return RedirectResponse(url=_safe_next(next), status_code=303)
        return templates.TemplateResponse(
            request,
            "login.html",
            {"request": request, "next": _safe_next(next), "error": None, "username": _username()},
        )

    @app.post("/login", response_class=HTMLResponse, name="login_submit")
    def login_submit(request: Request, username: str = Form(""), password: str = Form(""), next: str = Form("/channels")):
        if not _password():
            return _setup_required()
        ok_user = hmac.compare_digest(username.strip(), _username())
        ok_password = hmac.compare_digest(password, _password())
        if not (ok_user and ok_password):
            return templates.TemplateResponse(
                request,
                "login.html",
                {"request": request, "next": _safe_next(next), "error": "Incorrect username or password.", "username": username.strip()},
                status_code=401,
            )
        response = RedirectResponse(url=_safe_next(next), status_code=303)
        response.set_cookie(
            COOKIE_NAME,
            _make_token(),
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            secure=os.getenv("RENDER", "").lower() == "true",
            samesite="strict",
        )
        return response

    @app.get("/logout", name="logout")
    def logout():
        response = RedirectResponse(url="/login", status_code=303)
        response.delete_cookie(COOKIE_NAME)
        return response

    install_youtube_metrics(app)
    install_youtube_analytics(app)
    install_content_hub(app)
