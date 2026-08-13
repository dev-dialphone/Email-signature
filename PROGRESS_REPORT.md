# Progress Report — Email Signature System (continued)

Plain-language summary of everything built after the first research report.

## What we decided
- We are NOT touching anyone's Gmail settings via Google. Instead, a small
  **Chrome extension** adds the company signature **while the person writes an
  email**. This works on normal @gmail.com — no Google Workspace, no Google API,
  no login/permission from Google needed.

## What we built (a working app)
A standalone web app + a browser extension.

**1. The admin website** (runs in the browser)
- **Owner login** — can add, edit, and remove companies ("entities"). Each
  company has its own domain (e.g. everyone at `@yourcompany.com`).
- **Company admin login** — sees only their own company. They can:
  - Add / remove team members (name, email, title, phone).
  - Design ONE company signature: company name, logo (upload or link, with a
    size slider), address, website, phone, and social links.
  - Pick from **8 ready-made signature designs** (Classic, Modern, Minimal, Bold,
    Compact, Stacked, Stacked-social-bottom, Arranged).
  - See a **live preview** of exactly what recipients will get.
  - **Send test**, and **Save as Template** to reuse a design later.
  - Add **event/promo banners** (upload an image) that sit above or below the
    signature.
  - Click **Apply** to generate everyone's personalized signature.

**2. The clever bit — personalization**
- The admin builds ONE template with blanks. When a specific person sends mail,
  their OWN name and email are filled in automatically. Everyone's footer looks
  the same, signed with their own name.

**3. The browser extension** (installed on the employee's Chrome)
- When the employee clicks **Compose** in Gmail, the extension quietly fetches
  that person's company signature from our app and drops it into the draft.
- It figures out the right company automatically from the person's email address,
  so ONE extension serves ALL companies.

## What changed since the last report
- Removed the "Connect Google" requirement completely — the app no longer asks
  for any Google Workspace access. Apply just works.
- Added the full signature builder (8 designs, logo slider, live preview, send
  test, save-as-template gallery).
- Added multi-company support (owner manages companies; each admin isolated).
- Built and packaged the Chrome extension; baked in the live app address so there
  is nothing to configure.
- Fixed several app crashes (blank screen, login errors) caused by the server
  restarting or stale data.

## Current status — honest
- The **web app is fully working and tested**: designing, saving, applying, and
  the extension's data feed (`/api/resolve`) all return the correct personalized
  signature. Confirmed in the server logs.
- The **extension reaches the app correctly** (we can see its calls succeeding).
- **Still verifying:** the signature actually appearing inside the Gmail compose
  box on the user's machine. Two things to know:
  - The signature only appears **while composing a new email** — never in a
    received or already-sent message.
  - We added detailed on-screen logs to the extension to pinpoint any remaining
    injection issue.

## Important limitations of the extension approach
- Works only in **Chrome on that computer**, and only in the **Compose window**.
- Does not work on the Gmail mobile app or other email programs (Outlook).
- Each employee must install the extension once (can be pushed company-wide via
  managed-browser policy).

## If you ever move to Google Workspace
- The alternative "invisible" method (signature written straight into each
  person's Gmail settings, nothing to install) is still available as a built-in
  option — it just needs a paid Google Workspace domain and a one-time admin
  approval. The code seam for it is already in place.

## Files
- `app/` — the web app (admin site + backend).
- `extension/` — the Chrome extension.
- `uploads/entity-signature-extension.zip` — ready-to-install extension.
