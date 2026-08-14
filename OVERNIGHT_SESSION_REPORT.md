# Overnight Session Report (8 PM → 5 AM)

Plain-language summary of everything implemented in this session, in order.
All changes are committed and pushed to GitHub (`dev-dialphone/Email-signature`).

## 1. Pushed the whole project to GitHub + wrote the README
- Full, documented README (how it works, features, setup, API, limits).
- Commit: initial app + Gmail extension.

## 2. Deployed on the Coolify server
- Added the build config (Nixpacks + Python requirements) so Coolify can build
  and run the app on the port it provides.
- App went live at **https://signature.crownitsolution.com**.

## 3. Stopped data being wiped on every redeploy
- Made the database + uploaded images live in a **persistent volume** (`DATA_DIR`).
- Explained the two required Coolify settings: the `/data` volume AND the
  `DATA_DIR=/data` env var (the volume was the missing piece).
- Verified data survives a restart. Wrote a Coolify deploy guide.

## 4. Added Postgres as an option (SQLite stays default)
- One env var (`DATABASE_URL`) switches the app to Postgres; without it, SQLite.
- Fully tested the Postgres path on a real database.
- Advice: SQLite is enough for one office; Postgres is ready if it grows.

## 5. Pointed the extension at the live site
- Updated the Chrome extension from the old preview address to
  **https://signature.crownitsolution.com** and re-packaged the installer.

## 6. Fixed the confusing "Apply" behaviour
- Clarified there are TWO Apply buttons: Templates→Apply (loads a saved design)
  vs Apply & Status→"Apply signature to everyone" (the one that shows "Applied
  to N/N").
- The earlier "not working" was because the signature toggle was OFF and no
  employees were added — Apply correctly had nothing to do.
- Added clear on-screen messages ("turn signature ON", "add employees") and an
  inline "✓ Applied" status so nothing fails silently.

## 7. Fixed the promotional banner not showing
Several causes were found and addressed:
- **Proxy URL problem**: behind Coolify the app built image URLs as internal
  http:// links that Gmail blocked. Fixed to build absolute **HTTPS** URLs (set
  `PUBLIC_BASE_URL` env for a guaranteed result).
- **Wrong input type**: a `<canvas>`/HTML banner can't render in email — must be
  a plain image. Explained how to export to PNG.
- **Image too large**: Gmail refuses big images (a 1.7 MB banner failed while the
  small logo loaded). Added **automatic shrinking on upload** — resizes to
  ≤1000px and re-encodes heavy PNGs to JPEG (a 3.8 MB image becomes ~250 KB).

## 8. Improved the Promotions form
- Added a **"paste online image URL"** option and a **Preview** button that shows
  the image on the page before saving.
- Auto-converts a bare image URL or a GitHub `blob` page link into a proper
  email-safe image (and to the correct `raw.githubusercontent.com` link).
- Removed the raw-HTML box in favour of the cleaner URL input.

## 9. Login: show/hide password
- Added an eye-style "Show/Hide" toggle on the login password field.

## 10. Security & data-isolation testing (multi-tenant)
- Ran a full attack test with two companies (Alpha, Beta), separate admins.
- **Result: data does NOT mix or leak across companies.** Every admin sees only
  their own employees, signature, templates and promos; cross-company reads,
  deletes, applies, and domain-mismatched adds are all blocked; unauthenticated
  and forged-token requests are rejected (401); the extension endpoint returns
  only the correct company's signature.
- Two fixes from the test:
  - Cross-company employee delete now returns **404** (instead of a misleading
    success) so another company's data can't be probed.
  - The **modern** signature layout now shows the company name (was omitted).

## What the user still needs to do in Coolify
1. Ensure a **Persistent Storage** volume is mounted at **`/data`**.
2. Env vars: `DATA_DIR=/data`, `PUBLIC_BASE_URL=https://signature.crownitsolution.com`,
   `APP_SECRET=<random>` (plus optional `OWNER_EMAIL`/`OWNER_PASSWORD`).
3. **Redeploy** (Force deploy if a normal redeploy shows no change) — several UI
   fixes only appear after a fresh deploy.
4. Re-create the banner by **uploading the image file** (auto-shrunk) or pasting a
   small public image URL; Activate; Apply.

## Status at end of session
- App deployed and live; signature renders correctly for recipients.
- Data persistence, Postgres option, multi-tenant isolation: all in place/verified.
- Banner: fixed via auto-shrink + absolute HTTPS URLs; needs redeploy + a
  correctly-sized image.
- All work committed and pushed to GitHub.

## Still recommended
- Rotate the GitHub token shared during the session (treat as exposed).
- Confirm the domain's HTTPS certificate is valid.
