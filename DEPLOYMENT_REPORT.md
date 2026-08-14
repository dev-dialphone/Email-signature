# Deployment Report (continued)

Plain-language summary of everything done after the previous report — putting the
system live on a real server and getting it working with the organization's real
email.

## 1. Pushed the code to GitHub
- All code (web app + Chrome extension + docs) is now on GitHub:
  `github.com/dev-dialphone/Email-signature`.
- Wrote a full, well-documented README (how it works, features, setup, API,
  limitations).
- ⚠️ Reminder: the GitHub token shared in chat should be rotated (treat as exposed).

## 2. Deployed on the Coolify server
- Added the files Coolify needs to build and run the app (Nixpacks config +
  Python requirements). The app starts automatically on the port Coolify gives it.
- Deployment succeeded; the app is live at **https://signature.crownitsolution.com**.

## 3. Made the data survive redeploys
- Problem: by default the database lives inside the container and is wiped on
  every redeploy.
- Fix: the database + uploaded logos/banners now live in a **persistent volume**
  (set `DATA_DIR=/data` and add a `/data` storage volume in Coolify).
- Verified: created a company, restarted the app, the company was still there.
- Wrote a step-by-step Coolify deploy guide (`DEPLOY_COOLIFY.md`).

## 4. Added Postgres as an option (kept SQLite as default)
- The app can now run on **Postgres** by setting one environment variable
  (`DATABASE_URL`); if it's not set, it uses **SQLite** (simple, no extra server).
- Tested the Postgres path fully (login, companies, apply, extension feed,
  delete-with-cleanup) on a real Postgres database — all working.
- Recommendation given: **SQLite is enough for one office**; switch to Postgres
  only if it grows a lot. No code change needed to switch — just the env var.

## 5. Pointed the extension at the live site
- The extension was still pointing at the old temporary preview address.
- Updated it to the real domain **https://signature.crownitsolution.com** and
  re-packaged the installable zip (`uploads/entity-signature-extension.zip`).

## 6. Fixed the "Apply buttons not working" confusion
- What happened: with the real company, the **signature toggle was OFF** and the
  team list was empty, so "Apply" correctly had nothing to do — but the screen
  showed a confusing "Applied to undefined/undefined", making it look broken.
  (The extension popup even said the real reason: "signature disabled".)
- It was NOT a deployment bug — before, the test company had the signature ON and
  employees added, so it worked.
- Fix: the buttons now show a **clear message** instead of a confusing one:
  - "⚠ signature disabled — turn the signature ON in the Signature tab"
  - "⚠ No employees yet — add them in the Directory tab"
  - Template "Apply" now reports errors instead of failing silently.
- Verified: after turning the signature ON and adding an employee, **Apply works
  (1/1)** and the extension gets the correct personalized signature.

## What the user needs to do to go live
1. In the app: **Signature tab → Enabled = ON → Save**.
2. **Directory tab** → add the team members' emails.
3. **Apply & Status → Apply signature to everyone** → should say "Applied to N/N".
4. Redeploy in Coolify to pick up the clearer messages (optional).
5. In Gmail → **Compose** → the signature appears.

## Still open / recommended
- Confirm `https://signature.crownitsolution.com` has a valid HTTPS certificate so
  the extension can always reach it.
- Rotate the exposed GitHub token.
- Set `APP_SECRET` (random) and the owner login env vars for security.

## Current status
- App: **deployed and live**, data persists across redeploys.
- Database: SQLite (default) with Postgres ready via one env var.
- Extension: points at the live domain, packaged for install.
- Apply flow: working once the signature is enabled + employees added (now with
  clear on-screen guidance).
