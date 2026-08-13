"""App entrypoint. Serves the API and the single-file frontend. On first run it
seeds ONLY the platform owner (an empty app can't be bootstrapped otherwise);
override the owner credentials via OWNER_EMAIL / OWNER_PASSWORD env vars."""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import db
from .auth import hash_password
from .routes.api import router

app = FastAPI(title="Signature Manager")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

FRONTEND = Path(__file__).parent.parent / "frontend"
UPLOADS = Path(__file__).parent.parent / "uploads"


def seed():
    """Bootstrap the single platform owner if none exists. No demo tenants/users."""
    db.init_db()
    if db.q_one("SELECT id FROM users WHERE role='owner'"):
        return
    email = os.environ.get("OWNER_EMAIL", "owner@platform.com").lower()
    pw = os.environ.get("OWNER_PASSWORD", "owner123")
    db.execute("INSERT INTO users (id, tenant_id, email, name, title, phone, password_hash, role, created_at) "
               "VALUES (?,?,?,?,?,?,?,?,?)",
               (db.new_id(), None, email, "Platform Owner", "Owner", None,
                hash_password(pw), "owner", db.now_ms()))


@app.on_event("startup")
def _startup():
    seed()


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


# serve any other static asset (single-file app, but keep it flexible)
if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
UPLOADS.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS), name="uploads")
