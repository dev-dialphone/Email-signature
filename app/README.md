# Signature Manager — standalone multi-entity signature system

Admin designs **one** branded signature per entity → the app fetches each
employee's **name/email/title from their Google Workspace directory** and writes
a personalized signature into their Gmail. Employees do nothing. Supports
**multiple entities** (tenants) and **event/promo banners**.

## Run

```sh
python3 -m venv .venv && .venv/bin/pip install fastapi uvicorn pydantic python-multipart
cd app && ../.venv/bin/python -m uvicorn backend.main:app --port 8000
# open http://localhost:8000
```

On first run **only a platform owner** is seeded (no demo entities/employees):
- **Owner** `owner@platform.com` / `owner123` — override with `OWNER_EMAIL` /
  `OWNER_PASSWORD` env vars. The owner creates entities; each entity gets its own admin.

## Roles & flow
1. **Owner** → creates an entity (name + domain + admin). No Google connection needed —
   signatures are delivered by the Gmail browser extension (`../extension/`).
2. **Admin** → **Directory** tab: add employees (name/email/title/phone; email must be on
   the entity's domain). **Signature** tab: company details + layout + **logo upload**.
   **Promotions** tab: **upload a ready-made banner image** (or paste HTML) + activate.
3. **Admin** → **Apply** → signature pushed to every employee, personalized with their
   own name/email; **Apply & Status** shows per-user result + a preview.
4. **Employee** → nothing; signature appears (via Workspace `sendAs`, or the Gmail
   extension in `../extension/`).

## Google layer (the important seam)
`backend/google_provider.py` has two implementations behind one interface:
- **MockGoogleProvider** (default) — the "directory" is the admin-managed `employees`
  table (no fake data); signatures held in memory to prove the round-trip. Runs with
  **no Google account**.
- **RealGoogleProvider** — stubbed; shows exactly where the Directory API +
  `gmail.users.settings.sendAs.update` calls go. To go live:
  1. Google Cloud project → enable Admin SDK + Gmail API.
  2. Service account with **domain-wide delegation**; Workspace super-admin authorizes
     scopes `admin.directory.user.readonly`, `gmail.settings.basic`.
  3. `pip install google-api-python-client google-auth`, uncomment the calls,
     set `GOOGLE_MODE=real` and `GOOGLE_SA_JSON=/path/sa.json`.

**Only works on paid Google Workspace domains** (not personal @gmail.com).

## Structure
- `backend/db.py` — SQLite schema (tenants, users, sig_settings, promo_templates, sync_log).
- `backend/auth.py` — pbkdf2 passwords + HMAC session tokens + role guards.
- `backend/google_provider.py` — mock/real Google seam.
- `backend/lib/email_signature.py` + `sig_layouts*.py` — signature HTML renderer (8 layouts, ported from the extracted module).
- `backend/lib/sync.py` — the apply engine (fetch dir → render per user → push → log).
- `backend/routes/api.py` — all endpoints.
- `frontend/` — single-file vanilla-JS SPA (login, entities, signature editor, promotions, apply/status).

## Gmail browser extension (no Workspace needed)
`../extension/` — a Chrome MV3 extension that injects each employee's entity
signature into Gmail compose, resolving the entity by email domain via the
public `GET /api/resolve?email=` endpoint. Works on personal @gmail.com too.
See `../extension/README.md`.

## Not yet built (next)
- Real Google calls (currently stubbed).
- Scheduled auto re-sync (currently manual **Apply**).
- Per-user opt-out / audit history beyond last run.
