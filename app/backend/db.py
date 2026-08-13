"""SQLite schema + tiny data-access helpers. One file, no ORM — the domain is
small (6 tables) and stdlib sqlite3 keeps the standalone app zero-dependency on
the data layer. ponytail: single-DB, sync sqlite. Ceiling ~a few offices; move
to Postgres + async driver when tenants/users grow past that."""
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path

# DATA_DIR points at a persistent volume in production (set it in Coolify to the
# mounted path, e.g. /data). Falls back to the source dir for local dev. Keeping
# the DB off the container's ephemeral filesystem is what survives redeploys.
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "data.db"


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


SCHEMA = """
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT,
    google_connected INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    tenant_id TEXT,                       -- NULL for the platform owner
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    title TEXT,
    phone TEXT,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,                   -- owner | admin | agent
    created_at INTEGER NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS sig_settings (
    tenant_id TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 0,
    layout TEXT NOT NULL DEFAULT 'classic',
    logo_size TEXT NOT NULL DEFAULT 'large',
    logo_pos TEXT NOT NULL DEFAULT 'right',
    social_pos TEXT NOT NULL DEFAULT 'below_logo',
    company_name TEXT, tagline TEXT, address TEXT, website TEXT,
    logo_url TEXT, phone TEXT, email TEXT,
    facebook TEXT, twitter TEXT, youtube TEXT, linkedin TEXT, instagram TEXT,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS employees (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    email TEXT NOT NULL,
    name TEXT NOT NULL,
    title TEXT,
    phone TEXT,
    created_at INTEGER NOT NULL,
    UNIQUE (tenant_id, email),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS promo_templates (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    html TEXT NOT NULL,
    position TEXT NOT NULL DEFAULT 'above',   -- above | below (the signature)
    active INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS sig_templates (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    design_json TEXT NOT NULL,          -- {layout, logo_size, logo_pos, social_pos, company fields...}
    created_at INTEGER NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS sync_log (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    user_email TEXT NOT NULL,
    status TEXT NOT NULL,                     -- ok | error
    detail TEXT,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
"""

SIG_COLUMNS = [
    "enabled", "layout", "logo_size", "logo_pos", "social_pos",
    "company_name", "tagline", "address", "website", "logo_url", "phone", "email",
    "facebook", "twitter", "youtube", "linkedin", "instagram",
]


def now_ms() -> int:
    return int(time.time() * 1000)


def new_id() -> str:
    return str(uuid.uuid4())


def init_db() -> None:
    with _conn() as c:
        c.executescript(SCHEMA)


def q_one(sql: str, params: tuple = ()) -> dict | None:
    with _conn() as c:
        r = c.execute(sql, params).fetchone()
        return dict(r) if r else None


# Guarantee the schema exists the moment this module is imported, so a worker
# started against a missing/blank data.db self-heals instead of 500-ing on the
# first query. Cheap: CREATE TABLE IF NOT EXISTS is a no-op when present.
init_db()


def q_all(sql: str, params: tuple = ()) -> list[dict]:
    with _conn() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]


def execute(sql: str, params: tuple = ()) -> None:
    with _conn() as c:
        c.execute(sql, params)


def ensure_sig_row(tenant_id: str) -> dict:
    row = q_one("SELECT * FROM sig_settings WHERE tenant_id=?", (tenant_id,))
    if row is None:
        execute("INSERT INTO sig_settings (tenant_id) VALUES (?)", (tenant_id,))
        row = q_one("SELECT * FROM sig_settings WHERE tenant_id=?", (tenant_id,))
    return row
