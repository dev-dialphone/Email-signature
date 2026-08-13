# Standalone Email-Signature Platform — Implementation Plan

> **STATUS (2026-08-13):** Pivoted to the **Google Workspace auto-apply** model
> (admin sets one signature → pushed to every user's Gmail, name/email fetched
> from the directory). A working **multi-tenant v1** is built and running in
> `app/` with a **mock Google layer** (`google_provider.py`) so it runs with no
> real Workspace. Swap `GOOGLE_MODE=real` + a delegated service account to go
> live. The plan below is the original send-through-app design, kept for reference.
> See `app/README.md` for what actually shipped.

---


A self-contained web app for your office. Sales agents connect their own mailbox;
admin designs ONE branded company signature (+ event/promo templates); every mail
an agent sends through the platform goes out branded and auto-signed with **that
agent's own name & email**, pulled live from their connected account.

Reuses the extracted module (FastAPI + React) as the starting skeleton — it already
has the signature renderer, layouts, template CRUD and admin editor. We add: auth,
mailbox connection (Gmail/SMTP), a compose+send path, and promo templates.

---

## 1. Scope (what this system does)

- **Admin**: designs org signature (logo, socials, layout, address) + saves reusable
  **event/promotional templates**; toggles signature ON/OFF; manages agents.
- **Agent**: connects their email account once; composes & sends mail from the app;
  signature is stamped automatically with their own name/email — they never edit it.
- **Auto-personalization**: name + email come from the agent's connected account
  (never a stored copy) so it's always correct for whoever is sending.
- **Promo template**: admin picks an active event/promo banner; it's injected above
  or below the signature on every send until switched off.

Out of scope for v1 (add later): inbound/receive + lead matching, sequences,
Conversations timeline. This plan is **send-side + signature + promo** only.

---

## 2. Architecture

```
React (Vite + TS)  ──HTTP──►  FastAPI  ──►  Postgres (or SQLite for v1)
   admin editor                 auth / RBAC        org_settings (sig_*)
   agent compose+send           mailbox connect    users + mail_account
                                signature render    sig_templates
                                send dispatcher     promo_templates
                                       │
                                       ▼
                          Gmail API  /  SMTP (app-password)
```

- **Backend**: FastAPI + SQLAlchemy (async) + Alembic. Reuse `lib/email_signature.py`,
  `lib/sig_layouts*.py`, `routes/org_settings.py`, `routes/sig_templates.py`,
  `schemas/`. Rewrite imports (drop `..core`, `..rbac` app-specific paths).
- **Frontend**: React + TS. Reuse `EmailSignaturePanel`, `SigCanvas*`, `SigLayoutPicker`,
  gallery components, `sigLayouts.ts`, `sigCanvasToHtml.ts`.
- **DB v1**: SQLite (zero-ops for one office). Swap to Postgres by config later.

---

## 3. Data model (new + reused)

Reused (from module): `org_settings.sig_*`, `sig_templates`.

New tables:

- **users** — `id, email, name, title, phone, password_hash, role(admin|agent), is_active`
  (name/title/phone are the values stamped into the signature).
- **mail_account** — per-user mailbox connection:
  `user_id, provider(gmail|smtp), send_as_email, display_name,
   gmail_refresh_token(enc), smtp_host, smtp_port, smtp_user, smtp_pass(enc),
   status(connected|error), last_error`.
- **promo_templates** — `id, name, html, position(above|below), active(bool),
   starts_at, ends_at`. Only one active at a time (or date-gated).
- **sent_log** — `id, user_id, to, subject, provider, status, error, created_at`
  (honest send accounting — "sent" means genuinely sent).

Secrets (tokens/passwords) encrypted at rest (Fernet key from env).

---

## 4. Mailbox connection (the "connect their mail id" part)

Two providers, Gmail preferred (deliverability + real Sent folder):

**A. Gmail / Google Workspace (OAuth)**
1. Agent clicks "Connect Gmail" → Google OAuth consent (`gmail.send` scope; add
   `gmail.readonly` later for receive).
2. Store the **refresh token** (encrypted). `send_as_email` = their Google address.
3. Send via Gmail API `users.messages.send` (RFC-822 MIME, HTML body + signature).

**B. SMTP fallback (app password)**
1. Agent enters host/port/user/app-password → we verify by a test login.
2. Send via `aiosmtplib` over TLS.

**Honesty rule (from your CRM):** if a user is Gmail-connected, send ONLY via Gmail;
on failure, record a real failure in `sent_log` — never silently retry via another
pipe and report success.

---

## 5. Send flow (A + B together)

`POST /api/email/send  {to, subject, body}`
1. Load sender = `current_user`; load their `mail_account`.
2. Load `org_settings`. If `sig_enabled`: call
   `build_signature_html(org, user.name, mail_account.send_as_email, user.phone, user.title, base_url)`
   → always re-rendered per sender (existing behavior in `email_signature.py`).
3. If an active `promo_template`: inject its HTML at its `position`.
4. Assemble: `body_html` + `<hr>` + `promo?` + `signature`.
5. Dispatch through the sender's provider (Gmail API or SMTP).
6. Write `sent_log` (status + any error). Return real result to UI.

Injection point already documented in `email_inject_snippet.py` — mirror it.

---

## 6. Backend endpoints

- `POST /api/auth/login`, `GET /api/auth/me` (JWT).
- `GET/PATCH /api/org-settings`, `POST /api/org-settings/logo`  *(reused)*.
- `GET/POST/DELETE /api/sig-templates`, `POST /{id}/apply`  *(reused)*.
- `GET/POST/PATCH/DELETE /api/promo-templates`, `POST /{id}/activate`  *(new)*.
- `GET /api/mail/connect/gmail` (OAuth start) + `/callback`; `POST /api/mail/smtp` (save+verify); `GET /api/mail/status`  *(new)*.
- `POST /api/email/send`; `GET /api/email/sent` (log)  *(new)*.
- `GET/POST/PATCH /api/users` (admin manages agents)  *(new)*.

RBAC: `admin` = org-settings, templates, promos, users. `agent` = connect mailbox,
compose+send, read own sent log.

---

## 7. Frontend pages

- **Login**.
- **Settings → Email Signature** (admin) — reuse `EmailSignaturePanel` + canvas.
- **Settings → Saved Templates** (admin) — reuse gallery.
- **Settings → Promotions** (admin) — new: create/preview/activate event banners.
- **Settings → Users** (admin) — new: add agents, set name/title/phone.
- **My Mailbox** (agent) — new: Connect Gmail / enter SMTP; connection status.
- **Compose** (agent) — new: to/subject/body + live signature+promo preview + Send.
- **Sent** (agent) — new: send log.

---

## 8. Build order (milestones)

1. **Scaffold** — FastAPI app, SQLite, Alembic, JWT auth, users table, seed admin.
2. **Port signature module** — copy `lib/`, `routes/org_settings.py`,
   `sig_templates.py`, `schemas/`; rewrite imports; wire admin editor pages. Verify
   live preview + save works end-to-end.
3. **Mailbox connect** — SMTP first (fastest), then Gmail OAuth. `mail_account`, status UI.
4. **Send path** — `/api/email/send` with signature injection + `sent_log`; Compose UI.
   Verify a real test email arrives branded + personalized.
5. **Promo templates** — table, CRUD, activate, inject into send. Admin Promotions page.
6. **Polish** — RBAC hardening, secret encryption, error surfacing, logo absolute URLs.

---

## 9. Key decisions to confirm

- **Providers**: Gmail OAuth + SMTP both, or SMTP-only for v1? (Gmail needs a Google
  Cloud project + OAuth consent screen — ~1 day extra.)
- **DB**: SQLite (simplest for one office) OK, or Postgres from day 1?
- **Receive/inbox**: include in v1 or defer (this plan defers it)?
- **Promo template**: single active banner, or date-scheduled multiple?

---

## 10. Effort estimate (1 dev)

| Milestone | Est. |
|---|---|
| 1 Scaffold + auth | 1–2 d |
| 2 Port signature module | 1–2 d |
| 3 Mailbox connect (SMTP + Gmail) | 2–3 d |
| 4 Send path + Compose | 2 d |
| 5 Promo templates | 1–2 d |
| 6 Polish | 1–2 d |
| **Total** | **~8–13 d** |

SMTP-only + SQLite trims Gmail OAuth (~2 d) → v1 in ~6–8 d.
