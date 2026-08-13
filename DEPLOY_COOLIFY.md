# Deploying on Coolify (SQLite + persistent volume)

The app uses **SQLite** by default. To keep your data (companies, employees,
signatures, uploaded logos & banners) safe across every redeploy, store it on a
**persistent volume** and point `DATA_DIR` at it. This is the only thing you must
configure — no separate database to run.

Verified: with `DATA_DIR` on a persistent path, created data survives a full
app restart/redeploy.

---

## One-time setup in Coolify

### 1. Persistent Storage
App → **Persistent Storage** → **Add**:

| Field | Value |
|------|-------|
| Name | `sig-data` |
| Mount Path (in container) | `/data` |

This creates a volume on the host that is re-attached on every deploy.

### 2. Environment Variables
App → **Environment Variables** → add:

```
DATA_DIR=/data
APP_SECRET=<a long random string>
OWNER_EMAIL=admin@crownitsolution.com
OWNER_PASSWORD=crown@123
```

- `DATA_DIR=/data` → SQLite file becomes `/data/data.db`; uploads go to
  `/data/uploads/`. Both now live on the persistent volume.
- `APP_SECRET` → signs login sessions. **Set this** (any long random value).
- `OWNER_EMAIL` / `OWNER_PASSWORD` → the first login. Only applied when the DB is
  empty (first boot). See "Changing the owner later" below.

### 3. Deploy
Click **Deploy**. Watch logs for `Application startup complete`.

---

## Verify it persists
1. Log in, create a company.
2. Redeploy the app in Coolify.
3. Log in again → the company is still there. ✅

---

## Backups (recommended)
The whole database is one file: `/data/data.db`.
- Coolify → your server → the `sig-data` volume can be snapshotted/backed up.
- Or copy it out periodically: it is a normal SQLite file (`.db`), portable and
  openable with any SQLite tool.

---

## Changing the owner later
`OWNER_EMAIL` / `OWNER_PASSWORD` only seed the owner on a **fresh** database. If
you already deployed with the defaults and want to change them:
- Easiest: stop the app, delete `/data/data.db` (wipes all data), set the env
  vars, redeploy — a new owner is seeded.
- Or ask for a small "change password" screen to be added (no data loss).

---

## When to move to Postgres
SQLite is enough for one office / a handful of companies (read-heavy, few writes).
Move to Postgres only if you outgrow it (many companies with heavy concurrent
admin writing, or multiple app instances behind a load balancer). No code change
needed — just set `DATABASE_URL=postgresql://...` and redeploy. See `README.md`.
