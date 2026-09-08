# Email Signature Manager

A standalone, **multi-company** email-signature platform. An admin designs **one
branded signature** per company; every employee's Gmail **Compose** window
automatically shows it — personalized with that employee's own name & email — via
a lightweight **Chrome extension**.

**No Google Workspace, no Google API keys, no OAuth, no per-person setup.** Works
on ordinary `@gmail.com` accounts.

---

## Table of contents
- [How it works](#how-it-works)
- [Features](#features)
- [Architecture](#architecture)
- [Repository layout](#repository-layout)
- [Quick start (backend)](#quick-start-backend)
- [Install the Chrome extension](#install-the-chrome-extension)
- [Using the app](#using-the-app)
- [Roles & permissions](#roles--permissions)
- [Signature templates](#signature-templates)
- [API reference](#api-reference)
- [Data model](#data-model)
- [Testing](#testing)
- [Configuration](#configuration)
- [Limitations](#limitations)
- [Optional: Google Workspace auto-push](#optional-google-workspace-auto-push)

---

## How it works

```
Employee clicks "Compose" in Gmail
        │
        ▼
Chrome extension reads the signed-in Gmail address
        │
        ▼
GET /api/resolve?email=<address>
        │
        ▼
Backend resolves the COMPANY by the email domain,
renders that company's signature filled with the
employee's own name/email, adds any active promo banner
        │
        ▼
Extension injects the finished HTML into the compose draft ✅
```

The signature is **never stored per person** — it is re-rendered on every request
so each sender's details are always correct. Output is **table-based inline-CSS
HTML** that renders reliably in Gmail, Outlook, and Apple Mail.

---

## Features

- **19 email-safe signature templates** — a visual picker + **live preview**:
  Classic, Modern, Minimal, Bold, Compact, Stacked, Stacked-social-bottom,
  Arranged, Sidebar, Banner-top, Elegant, Card, Photo-circle, Banner,
  CTA-button, QR-card, Promo-banner, Dark, and **Salamtalk** (a large-title
  brand layout with a blue left band + outline social circles).
- **Per-entity themes** — each company (by email domain) can get its own accent
  colour, social-icon style and default layout, so no two companies' signatures
  look alike (see `sig_theme.py`). Unknown domains fall back to the default look.
- **Company fields**: name, tagline, address, website, phone, email, and 5 social
  links (Facebook, X/Twitter, YouTube, LinkedIn, Instagram — each optional).
- **Logo**: file upload with a size control (Small 120 / Medium 180 / Large 240,
  or a custom pixel slider 60–500). Width-only sizing; the live preview resizes
  the logo **in place** so social icons never reload or flicker.
- **Inlined social icons** — every social glyph is a base64 data-URI, so icons
  render reliably in the live preview **and** in every email client with no CDN
  dependency.
- **Employees / recipients**: add, **edit in place** (no delete + recreate), or
  remove. Edit is available on both the **Directory** and **Apply & Status**
  tabs as a clean labelled form; email edits are re-validated against the entity
  domain.
- **Per-sender personalization**: each employee's own name/email is stamped into
  the signature at render time (never stored per person).
- **Event / promotional banners**: upload an image, place it above or below the
  signature, one active at a time.
- **Saved-template gallery**: save a design, re-apply or delete later.
- **Per-agent export**: Copy-for-Gmail (rich clipboard), Download `.html`, or PNG
  image — for any employee, ready to paste.
- **Send test** — render the exact recipient view for the logged-in admin.
- **Multi-company (multi-tenant)**: one backend + one extension serve every
  company; the company is resolved from the sender's email domain.
- **Role-based access**: platform owner vs company admin, fully isolated per
  company.
- **First-run seeding**: the platform owner is always seeded; the **Salamtalk**
  entity is seeded with its finished signature as a worked example.
- **Cache-busted UI**: `index.html` serves `app.js?v=<mtime>` with a `no-cache`
  header, so new UI never hides behind a stale browser cache.

---

## Architecture

| Layer | Tech | Notes |
|------|------|-------|
| Backend | **FastAPI** (Python 3.11) | one router, ~single-file modules |
| Database | **Postgres** (set `DATABASE_URL`) or **SQLite** (default) | same schema; one env var switches |
| Auth | pbkdf2 password hash + HMAC session tokens | no external auth lib |
| Frontend | **Vanilla JS SPA** (no build step) | served by the backend |
| Delivery | **Chrome MV3 extension** | injects into Gmail compose |
| Google seam | `google_provider.py` | Mock (default) / Real (Workspace) |

---

## Repository layout

```
app/
  backend/
    main.py              # app entry, seeds the platform owner, serves SPA + /uploads
    db.py                # SQLite schema + helpers (self-heals schema on import)
    auth.py              # password hashing + session tokens + role guards
    google_provider.py   # Mock/Real Google seam (directory + signature push)
    routes/api.py        # all HTTP endpoints
    lib/
      email_signature.py     # build_signature_html() — renders a signature
      sig_icons.py           # inlined base64 social-icon data-URIs (no CDN)
      sig_theme.py           # per-entity accent / icon-style / layout, by domain
      sig_layouts.py         # classic / modern / minimal / bold / compact + registry
      sig_layouts_extra.py   # stacked / stacked_social_bottom
      sig_layout_arranged.py # arranged (independent logo/social placement)
      sig_layouts_pro.py     # sidebar / banner_top / elegant / card / photo_circle / banner_hex
      sig_layouts_v2.py      # cta_button / qr_card / promo_banner / dark
      sig_layout_salamtalk.py# salamtalk_pro (blue band + outline circles)
      sig_cta.py             # derive CTA link + QR image from website/email
      sync.py                # apply engine: render per employee + store + log
  frontend/
    index.html           # SPA shell + styles (cache-busts app.js)
    app.js               # SPA logic (login, owner + admin views, inline edit)
  run.sh                 # launcher (uses $PORT for the preview proxy)
  README.md              # app-specific notes

extension/
  manifest.json          # MV3 manifest
  content.js             # detects compose, fetches signature, injects
  popup.html / popup.js  # set backend URL + test
  icon.png
  README.md              # extension-specific notes

RESEARCH_SUMMARY.md / IMPLEMENTATION_PLAN.md / PROGRESS_REPORT.md / FINAL_REPORT.md
                         # plain-language design & progress notes
```

---

## Quick start (backend)

Requires Python 3.11+.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# (fastapi, uvicorn[standard], pydantic, python-multipart, psycopg[binary], pillow)

cd app
../.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
# open http://localhost:8000
```

On first run the app seeds:

- **Platform owner:** `owner@platform.com` / `owner123`
  (override with `OWNER_EMAIL` / `OWNER_PASSWORD` env vars)
- **Salamtalk** entity — a worked example, with its finished signature applied.
  Admin: `accounts@salamtalk.com` / `salamtalk123`
  (override the password with `SALAMTALK_ADMIN_PASSWORD`). Seeding is idempotent
  — it's skipped if the `salamtalk.com` tenant already exists.

The owner creates further companies; each company gets its own admin login.

---

## Install the Chrome extension

The extension must live on the **machine running Chrome** (not a server).

1. Copy the `extension/` folder to that machine (or unzip
   `uploads/entity-signature-extension.zip` if provided).
2. Chrome → `chrome://extensions` → enable **Developer mode**.
3. **Load unpacked** → select the `extension/` folder (the one with `manifest.json`).
4. Click the extension icon → set **Backend URL** to your deployed app URL →
   open a Gmail tab → **Save & Test**. Expect `✓ <email> → <company>`.
5. In Gmail, click **Compose** → the signature appears at the bottom of the draft.

> The default backend URL is baked into `content.js` / `popup.js`. Change it there
> (or via the popup) when you deploy to a new host.

**Company-wide rollout:** push via Chrome Enterprise policy
(`ExtensionInstallForcelist`) so it installs silently on all machines.

---

## Using the app

**Owner**
1. Log in → **Entities** tab → **Add entity** (company name + domain + admin creds).
2. Edit or remove companies anytime.

**Company admin**
1. Log in (credentials the owner set).
2. **Signature** tab → *Fields* (company info + logo) and *Design* (pick a
   template, live preview) → **Save**. Optionally **Send test** / **Save as Template**.
3. **Templates** tab → apply/delete saved designs.
4. **Directory** tab → add/remove team members (email must be on the company domain).
5. **Promotions** tab → upload a banner image → **Activate**.
6. **Apply & Status** → **Apply** to generate everyone's personalized signature.

**Employee** — install the extension once, then just compose. Nothing else.

---

## Roles & permissions

| Action | Owner | Company admin |
|-------|:----:|:----:|
| Add / edit / remove companies | ✅ | ❌ |
| Manage own team (employees) | ❌ | ✅ (own company only) |
| Design signature / promos | ❌ | ✅ (own company only) |
| Apply signatures | ❌ | ✅ (own company only) |
| See other companies' data | — | ❌ |

Every admin/agent action is scoped to the caller's `tenant_id`; the owner is
cross-company. `/api/resolve` is public (the extension only ever knows the current
user's address).

---

## Signature templates

All are `<table>`-based inline-CSS HTML (no flexbox/grid, no external styles).
Every user value is HTML-escaped; logo URLs are made absolute; social icons are
**inlined base64** (no CDN). Registered in `sig_layouts.py`'s `LAYOUTS`; the
admin's picked layout always wins over the entity theme default.

**Core** (`sig_layouts.py`, `sig_layouts_extra.py`, `sig_layout_arranged.py`)
1. **Classic** — name/title/contact left, logo + socials right.
2. **Modern** — logo beside name, accent bar, contact on one dotted line.
3. **Minimal** — name · title side by side, one contact line, logo far right.
4. **Bold** — thick accent left border, large name, logo down the right.
5. **Compact** — two lines only, socials + logo.
6. **Stacked** / 7. **Stacked (social bottom)** — single column variants.
8. **Arranged** — logo position (right/below) + social position independent.

**Pro** (`sig_layouts_pro.py`)
9. **Sidebar** · 10. **Banner-top** · 11. **Elegant** · 12. **Card** ·
13. **Photo-circle** · 14. **Banner**.

**Distinct / 2026 trends** (`sig_layouts_v2.py`)
15. **CTA-button** (pill CTA) · 16. **QR-card** (scan-to-connect) ·
17. **Promo-banner** (full-width strip) · 18. **Dark** (inverted).

**Brand** (`sig_layout_salamtalk.py`)
19. **Salamtalk** — 6px blue left band, large title, big logo, outline social
   circles; driven by entity values so any company can use it.

Adding a layout: write a function taking `SigVals`, register it in a
`*_LAYOUTS` dict, and (for a new module) add one import + spread in
`_register_extra()`. Add a Design-picker tile in `app.js`'s `LAYOUTS` array.

---

## API reference

Base path: `/api`. All admin routes require a Bearer session token.

**Auth**
- `POST /auth/login` → `{token, user}`
- `GET  /auth/me`

**Entities (owner)**
- `GET /tenants` · `POST /tenants` · `PATCH /tenants/{id}` · `DELETE /tenants/{id}`

**Signature (admin)**
- `GET /signature` · `PATCH /signature`
- `GET /signature/preview` (saved) · `POST /signature/preview` (unsaved draft)
- `POST /signature/test` · `GET /signature/export` (by `employee_id` or `email`)
- `POST /signature/logo` (multipart image upload)

**Saved templates (admin)**
- `GET /sig-templates` · `POST /sig-templates`
- `POST /sig-templates/{id}/apply` · `DELETE /sig-templates/{id}`

**Team / directory (admin)**
- `GET /employees` · `POST /employees` · `PATCH /employees/{id}` (edit in place)
  · `DELETE /employees/{id}`

**Promotions (admin)**
- `GET /promos` · `POST /promos` · `POST /promos/upload`
- `POST /promos/{id}/activate` · `POST /promos/{id}/deactivate` · `DELETE /promos/{id}`

**Apply / status (admin)**
- `GET /directory` · `POST /apply` · `GET /sync-log` · `GET /verify/{email}`

**Extension (public)**
- `GET /resolve?email=<addr>` → `{found, entity, name, html}`

---

## Data model

Tables (identical on SQLite & Postgres; all company data cascades on entity delete):

- `tenants` — companies (`name`, `domain`, …)
- `users` — logins (`owner` | `admin`), scoped by `tenant_id`
- `sig_settings` — one signature config per company (layout, logo, company fields, socials)
- `employees` — team directory per company (name/email/title/phone)
- `sig_templates` — saved signature designs (`design_json`)
- `promo_templates` — banners (`html`, `position`, `active`)
- `sync_log` — last apply run per company

---

## Testing

No external test framework — `tests/api_test.py` spins the app in-process with
FastAPI's `TestClient` and exercises every endpoint, RBAC, multi-tenant
isolation, per-entity themes, employee edit, logo sizing and signature rendering
with plain asserts.

```sh
.venv/bin/python tests/api_test.py      # prints PASS/FAIL per check + a summary
```

Runs against SQLite by default; set `DATABASE_URL` to also cover Postgres.

---

## Configuration

| Env var | Default | Purpose |
|--------|---------|---------|
| `OWNER_EMAIL` | `owner@platform.com` | seeded owner login |
| `OWNER_PASSWORD` | `owner123` | seeded owner password |
| `SALAMTALK_ADMIN_PASSWORD` | `salamtalk123` | seeded Salamtalk admin password |
| `APP_SECRET` | `dev-insecure-change-me` | HMAC key for session tokens (**set in prod**) |
| `DATABASE_URL` | *(unset → SQLite)* | `postgresql://user:pass@host:5432/db` to use Postgres |
| `DATA_DIR` | source dir | SQLite mode: persistent path for `data.db`; also holds uploads in both modes |
| `GOOGLE_MODE` | *(unset → mock)* | set to `real` to use the Workspace push path |
| `GOOGLE_SA_JSON` | — | service-account JSON path (real mode) |

---

## Limitations

- **Chrome + Compose window only.** Not the Gmail mobile app, not Outlook.
- Signature appears in **new drafts** — not retroactively in sent/received mail.
- Each employee installs the extension once (or via managed-browser policy).
- Employee email domain must be a **registered company**; unknown users on a known
  domain get a name derived from their address.
- Content-script selectors depend on Gmail's DOM; update `SELECTORS` in
  `content.js` if Gmail changes its compose markup.

---

## Optional: Google Workspace auto-push

For companies on **paid Google Workspace**, an "invisible" delivery mode exists:
the signature is written straight into each user's Gmail settings via the Admin
SDK + Gmail `settings.sendAs` API — **no extension to install**.

`app/backend/google_provider.py` contains a `RealGoogleProvider` stub showing the
exact calls. To enable:

1. Create a Google Cloud project → enable Admin SDK + Gmail API.
2. Create a service account with **domain-wide delegation**; a Workspace
   super-admin authorizes scopes `admin.directory.user.readonly`,
   `gmail.settings.basic`.
3. `pip install google-api-python-client google-auth`, fill in the stub, set
   `GOOGLE_MODE=real` and `GOOGLE_SA_JSON=/path/sa.json`.

This path only works on Workspace domains (not personal `@gmail.com`).
