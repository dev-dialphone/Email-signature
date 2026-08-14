# Post-Deployment Fixes Report

Plain-language summary of everything done after the previous (deployment) report —
fixing the issues found while testing the live site with the real organization
email.

## 1. Data-loss on redeploy — explained
- The persistent-storage code was already in place, but it only works once **two**
  things are set in Coolify:
  1. an env var `DATA_DIR=/data` (you had this), AND
  2. an actual **Persistent Storage volume mounted at `/data`** (this was the
     missing piece).
- Clarified that the env var alone doesn't save data — the volume is what makes
  `/data` survive redeploys. Once both are set, data persists.

## 2. Postgres option added (SQLite still default)
- The app can now run on **Postgres** by setting one env var (`DATABASE_URL`);
  without it, it stays on **SQLite**.
- Tested the Postgres path fully on a real database.
- Advice given: SQLite on the persistent volume is enough for one office; Postgres
  is there if it grows — no code change, just the env var.

## 3. Extension pointed at the live domain
- Updated the Chrome extension from the old temporary preview address to the real
  site **https://signature.crownitsolution.com** and re-packaged the installer.

## 4. "Apply buttons not working" — root cause found
- It was **not** a deployment bug. Two different buttons were being confused:
  - **Templates tab → Apply** = loads a saved design into the signature (then opens
    the Signature tab). It never showed "Applied to N/N".
  - **Apply & Status tab → Apply signature to everyone** = the one that shows
    "Applied to N/N".
- The real blocker earlier: the signature toggle was **OFF** and no employees were
  added, so Apply correctly had nothing to do — but the screen showed a confusing
  "undefined/undefined".
- Fixes:
  - Apply now shows clear guidance ("turn the signature ON", "add employees").
  - Templates Apply now shows an inline "✓ Applied" / "✗ error" message instead of
    a silent tab switch.

## 5. Promotional banner not visible (broken image) — fixed
- Cause: behind Coolify's proxy the app built the banner image URL as an
  **internal http:// address**, which Gmail blocks — so recipients saw a broken
  image icon (the signature itself rendered fine).
- Fix: the app now builds a proper **absolute HTTPS URL** for banner/logo images
  (via a new helper that honors a `PUBLIC_BASE_URL` env var, the proxy's headers,
  or upgrades to https automatically).
- Action needed in Coolify: set env var
  `PUBLIC_BASE_URL=https://signature.crownitsolution.com` and redeploy.
- Note: banners uploaded **before** the persistent volume existed were wiped and
  must be re-uploaded.

## 6. Added "paste image URL" option for banners
- The New Banner form now accepts a **direct image URL** (e.g. a GitHub raw link),
  in addition to file upload and raw HTML. A "Use URL" button builds the banner
  and shows a preview.
- External https image URLs render directly in email (they bypass the proxy path
  entirely), so this is the most reliable way to add a banner.
- Also explained how to get a GitHub **raw** image URL
  (`raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>`, repo must be public).

## What the user must do in Coolify (to finish)
1. **Persistent Storage** → add a volume mounted at `/data` (if not already).
2. **Environment Variables** → ensure:
   - `DATA_DIR=/data`
   - `PUBLIC_BASE_URL=https://signature.crownitsolution.com`
   - `APP_SECRET=<random>` (security)
3. **Redeploy** (Force deploy if a normal redeploy shows no change).
4. Re-upload the banner (or paste an image URL), Activate it.
5. Signature tab → **Enabled = ON**; Directory → add employees; Apply & Status →
   **Apply signature to everyone**.

## Current status
- Deployed and live at https://signature.crownitsolution.com.
- Signature renders correctly for recipients (name, title, contact, logo).
- Banner fix + image-URL option shipped; needs `PUBLIC_BASE_URL` + redeploy to show.
- Data persistence depends on the `/data` volume being present.
- All changes committed and pushed to GitHub (`dev-dialphone/Email-signature`).

## Still recommended
- Rotate the GitHub token shared earlier (treat as exposed).
- Confirm the HTTPS certificate on the domain is valid.
