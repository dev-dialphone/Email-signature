# Entity Signature — Gmail Chrome Extension

Injects the employee's **entity-specific** branded signature into every Gmail
compose window, personalized with their own name/email. Works on personal
`@gmail.com` **and** Google Workspace — no admin delegation, no OAuth needed.
Multi-entity: the backend resolves which entity by the employee's email domain.

## How it works
```
Employee opens Gmail → content.js detects a compose window
  → reads the signed-in address from the page
  → GET {backend}/api/resolve?email=<addr>
  → backend maps domain → entity, renders that entity's signature with the
    employee's name/email → returns HTML
  → content.js appends it into the compose body (once per compose)
```

## Install (unpacked, for testing)
1. Start the backend (see `../app/README.md`) — default `http://localhost:8000`.
2. Chrome → `chrome://extensions` → enable **Developer mode** →
   **Load unpacked** → select this `extension/` folder.
3. Click the extension icon → set **Backend URL** → **Save & Test**
   (open a Gmail tab first so it can detect your address).
4. In Gmail, click **Compose** → the signature appears in the body.

## Distribute to employees
- **Manual:** share the folder / a packed `.crx`; each employee loads it once.
- **Managed (recommended for an office):** force-install via Chrome Enterprise
  policy (`ExtensionInstallForcelist`) so it deploys silently to all machines.
- Point `host_permissions` + the popup **Backend URL** at your real backend host
  (replace `http://localhost:8000` with your deployed HTTPS URL).

## Multi-entity
Register each entity (Owner UI) with its domain — `sales-co.com`, `promo-co.com`,
etc. Same extension serves everyone; the resolve endpoint returns the right
entity's signature per employee. Admin edits a template → picked up on next compose.

## Known limits (ponytail)
- Gmail web only — not the mobile app, not Outlook/other clients.
- Selectors in `content.js` (`SELECTORS`) depend on Gmail's DOM; update if Gmail
  changes its compose markup. No official compose API exists.
- Injects per-compose into the message body (not the permanent Gmail Signature
  settings box). For that permanent box you need the Workspace `sendAs` API route
  (`../app/backend/google_provider.py` → RealGoogleProvider).
- `/api/resolve` is unauthenticated by design (extension only knows the current
  user's address). Add an API key / rate-limit before public deployment.
