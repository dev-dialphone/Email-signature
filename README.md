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
- [The 8 signature templates](#the-8-signature-templates)
- [API reference](#api-reference)
- [Data model](#data-model)
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

- **8 email-safe signature templates** (Classic, Modern, Minimal, Bold, Compact,
  Stacked, Stacked-social-bottom, Arranged) — visual picker + live preview.
- **Company fields**: name, tagline, address, website, phone, email, and 5 social
  links (Facebook, X/Twitter, YouTube, LinkedIn, Instagram — each optional).
- **Logo**: file upload with a size control (Small 120 / Medium 180 / Large 240,
  or a custom pixel slider 60–500). Width-only sizing so height auto-scales.
- **Per-sender personalization**: `{{AGENT_NAME}}`, `{{AGENT_EMAIL}}`, etc. filled
  at compose time.
- **Event / promotional banners**: upload an image, place it above or below the
  signature, one active at a time.
- **Saved-template gallery**: save a design, re-apply or delete later.
- **Send test** — render the exact recipient view for the logged-in admin.
- **Multi-company (multi-tenant)**: one backend + one extension serve every
  company; the company is resolved from the sender's email domain.
- **Role-based access**: platform owner vs company admin, fully isolated per
  company.

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
      email_signature.py # build_signature_html() — renders a signature
      sig_layouts.py     # classic / modern / minimal / bold / compact
      sig_layouts_extra.py     # stacked / stacked_social_bottom
      sig_layout_arranged.py   # arranged (independent logo/social placement)
      sync.py            # apply engine: render per employee + store + log
  frontend/
    index.html           # SPA shell + styles
    app.js               # SPA logic (login, owner + admin views)
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
.venv/bin/pip install fastapi uvicorn pydantic python-multipart

cd app
../.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
# open http://localhost:8000
```

On first run **only a platform owner** is seeded (no demo companies):

- **Owner:** `owner@platform.com` / `owner123`
  (override with `OWNER_EMAIL` / `OWNER_PASSWORD` env vars)

The owner creates companies; each company gets its own admin login.

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

## The 8 signature templates

All are `<table>`-based inline-CSS HTML (no flexbox/grid, no external styles).

1. **Classic** — two columns: name/title/contact left, logo + socials right.
2. **Modern** — logo beside name, accent bar, contact on one dotted line.
3. **Minimal** — name · title side by side, one contact line, logo far right.
4. **Bold** — thick accent left border, large name, logo down the right.
5. **Compact** — two lines only (name·title / phone·email·web), socials + logo.
6. **Stacked** — single column, socials by name, logo inline at bottom.
7. **Stacked (social bottom)** — same, socials under the logo.
8. **Arranged** — pick logo position (right/below) and social position
   (next-to-name / below-logo / bottom) independently.

Shared styling: accent `#1a73e8`, text `#333`, muted `#888`; social icons are
white glyphs on brand-colored circles; all user values are HTML-escaped; logo
URLs are made absolute so they render in remote clients.

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
- `GET /signature/preview` · `POST /signature/test`
- `POST /signature/logo` (multipart image upload)

**Saved templates (admin)**
- `GET /sig-templates` · `POST /sig-templates`
- `POST /sig-templates/{id}/apply` · `DELETE /sig-templates/{id}`

**Team / directory (admin)**
- `GET /employees` · `POST /employees` · `DELETE /employees/{id}`

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

## Configuration

| Env var | Default | Purpose |
|--------|---------|---------|
| `OWNER_EMAIL` | `owner@platform.com` | seeded owner login |
| `OWNER_PASSWORD` | `owner123` | seeded owner password |
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
