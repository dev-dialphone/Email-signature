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

from .db import DATA_DIR
FRONTEND = Path(__file__).parent.parent / "frontend"
UPLOADS = DATA_DIR / "uploads"


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


def seed_salamtalk():
    """Seed the Salamtalk entity with its finished signature exactly as designed
    (sidebar layout, brand-blue accent + outline icons from the domain theme).
    Idempotent: skips if the salamtalk.com tenant already exists."""
    db.init_db()
    if db.q_one("SELECT id FROM tenants WHERE domain=?", ("salamtalk.com",)):
        return
    tid = db.new_id()
    db.execute("INSERT INTO tenants (id, name, domain, google_connected, created_at) VALUES (?,?,?,?,?)",
               (tid, "Salamtalk", "salamtalk.com", 0, db.now_ms()))
    db.ensure_sig_row(tid)
    db.execute("INSERT INTO users (id, tenant_id, email, name, title, phone, password_hash, role, created_at) "
               "VALUES (?,?,?,?,?,?,?,?,?)",
               (db.new_id(), tid, "accounts@salamtalk.com", "Accounts Department", "Accounts Team",
                "+1 (914) 904-7785", hash_password(os.environ.get("SALAMTALK_ADMIN_PASSWORD", "salamtalk123")),
                "admin", db.now_ms()))
    sig = {
        "enabled": 1, "layout": "sidebar", "logo_size": "large",
        "company_name": "Salamtalk",
        "address": "Dubai Headquarters Building A1, Dubai Digital Park, Dubai Silicon Oasis, UAE",
        "website": "https://www.salamtalk.com",
        "logo_url": "https://raw.githubusercontent.com/dialphonegit/Diaphone_logo/main/salamtalk.jpeg",
        "phone": "+1 (914) 904-7785",
        "facebook": "https://www.facebook.com/salamtalk",
        "twitter": "https://x.com/salamtalk",
        "youtube": "https://www.youtube.com/@salamtalk",
        "linkedin": "https://www.linkedin.com/company/salamtalk/",
        "instagram": "https://www.instagram.com/salamtalk.fzco",
    }
    sets = ", ".join(f"{k}=?" for k in sig)
    db.execute(f"UPDATE sig_settings SET {sets} WHERE tenant_id=?", (*sig.values(), tid))


@app.on_event("startup")
def _startup():
    seed()
    seed_salamtalk()


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


# serve any other static asset (single-file app, but keep it flexible)
if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
UPLOADS.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS), name="uploads")
