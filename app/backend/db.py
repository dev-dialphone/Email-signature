"""Data layer. Speaks Postgres when DATABASE_URL is set, else SQLite (local dev).

The app's route code calls q_one / q_all / execute with '?' placeholders and a
tuple; this module translates to the active driver. Schema is identical across
both engines (portable TEXT/INTEGER columns), so nothing above this file changes
when you flip databases.

ponytail: hand-rolled thin layer, no ORM/pool tuning. Fine for one-office scale;
add a real connection pool (psycopg_pool) if concurrency grows."""
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_PG = DATABASE_URL.startswith(("postgres://", "postgresql://"))

# DATA_DIR (SQLite mode) points at a persistent volume in production; also holds
# uploaded logos/banners in BOTH modes (see routes/api.py, main.py).
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "data.db"

if USE_PG:
    import psycopg
    from psycopg.rows import dict_row


# ---- schema (portable; '%%' not needed — no literal % in DDL) ----
SCHEMA = """
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT,
    google_connected INTEGER NOT NULL DEFAULT 0,
    created_at BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    tenant_id TEXT,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    title TEXT,
    phone TEXT,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at BIGINT NOT NULL,
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
    whatsapp TEXT,
    teams TEXT,
    created_at BIGINT NOT NULL,
    UNIQUE (tenant_id, email),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS promo_templates (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    html TEXT NOT NULL,
    position TEXT NOT NULL DEFAULT 'above',
    active INTEGER NOT NULL DEFAULT 0,
    created_at BIGINT NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS sig_templates (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    design_json TEXT NOT NULL,
    created_at BIGINT NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS sync_log (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    user_email TEXT NOT NULL,
    status TEXT NOT NULL,
    detail TEXT,
    created_at BIGINT NOT NULL,
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


# ---- placeholder translation: routes use '?'; Postgres wants '%s' ----
def _sql(sql: str) -> str:
    return sql.replace("?", "%s") if USE_PG else sql


def _pg_conn():
    # client_encoding=UTF8 so TEXT always decodes to str (a SQL_ASCII server can
    # otherwise hand back bytes, breaking password checks / JSON).
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, client_encoding="UTF8")


def _sqlite_conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


# Columns added after the first release; self-heal existing DBs on boot so a
# redeploy never needs a manual migration. (table, column, type).
_MIGRATIONS = [
    ("employees", "whatsapp", "TEXT"),
    ("employees", "teams", "TEXT"),
]


def _migrate(run) -> None:
    """Add any missing column via ALTER TABLE. `run` executes one SQL string.
    'duplicate column' errors are expected when the column already exists."""
    for table, col, typ in _MIGRATIONS:
        try:
            run(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
        except Exception:
            pass  # already present


def init_db() -> None:
    if USE_PG:
        with _pg_conn() as c, c.cursor() as cur:
            cur.execute(SCHEMA)      # psycopg runs multiple statements in one execute
            for table, col, typ in _MIGRATIONS:
                try:
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {typ}")
                except Exception:
                    c.rollback()
            c.commit()
    else:
        with _sqlite_conn() as c:
            c.executescript(SCHEMA)
            _migrate(lambda s: c.execute(s))


def q_one(sql: str, params: tuple = ()) -> dict | None:
    if USE_PG:
        with _pg_conn() as c, c.cursor() as cur:
            cur.execute(_sql(sql), params)
            r = cur.fetchone()
            return dict(r) if r else None
    with _sqlite_conn() as c:
        r = c.execute(sql, params).fetchone()
        return dict(r) if r else None


def q_all(sql: str, params: tuple = ()) -> list[dict]:
    if USE_PG:
        with _pg_conn() as c, c.cursor() as cur:
            cur.execute(_sql(sql), params)
            return [dict(r) for r in cur.fetchall()]
    with _sqlite_conn() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]


def execute(sql: str, params: tuple = ()) -> None:
    if USE_PG:
        with _pg_conn() as c, c.cursor() as cur:
            cur.execute(_sql(sql), params)
            c.commit()
        return
    with _sqlite_conn() as c:
        c.execute(sql, params)


def ensure_sig_row(tenant_id: str) -> dict:
    row = q_one("SELECT * FROM sig_settings WHERE tenant_id=?", (tenant_id,))
    if row is None:
        execute("INSERT INTO sig_settings (tenant_id) VALUES (?)", (tenant_id,))
        row = q_one("SELECT * FROM sig_settings WHERE tenant_id=?", (tenant_id,))
    return row


# Create the schema on import so a fresh DB self-heals before the first query.
init_db()
