# Banner Troubleshooting Report

Plain-language summary of everything done after the previous report — all focused
on the **promotional banner not showing** (broken "promotion" image icon in the
signature). The signature itself renders correctly; only the banner image fails.

## What we improved in the app
1. **Added a "paste image URL" option** to the New Banner form (with a "Use URL"
   button), so a banner can be added by URL instead of only file upload.
2. **Made banner input forgiving**: if you paste a bare image URL — or a GitHub
   `github.com/.../blob/...` page link — into the banner box, the app now
   auto-converts it into a proper `<img>` and rewrites `blob` → real
   `raw.githubusercontent.com` link so it can render in email.
3. (Earlier) Added absolute-HTTPS URL building for images behind the Coolify proxy
   (needs `PUBLIC_BASE_URL` env set + redeploy).

## What we diagnosed
The broken banner is **always an image-source problem**, not a signature problem.
The image the banner points to cannot be loaded by Gmail. The likely causes, in
order:

1. **The banner was a canvas/HTML design, not an image.** One banner the user had
   was a `<canvas>` element (a picture drawn by JavaScript). Email clients strip
   JavaScript/canvas, so it shows nothing. → Must export the canvas as a PNG and
   upload that instead.
2. **The uploaded image file was wiped.** Files uploaded before the `/data`
   persistent volume existed were deleted on redeploy, so their URL now 404s.
3. **The image URL is internal/`http://`** (proxy) or **behind Cloudflare**, which
   blocks it → Gmail shows a broken icon.

## What the user still needs to provide
To pin the exact cause we need the **actual broken image URL**:
- In Gmail, right-click the broken "promotion" image → **Copy image address** →
  share that URL. It immediately tells us whether it's a 404, an http/internal
  URL, or a Cloudflare block.

## The reliable fix (recommended path)
1. If the banner is a canvas/HTML design → **export it as a PNG** first.
2. **Delete** the current "batic" banner.
3. Create a new banner by **uploading the PNG** (the app hosts it and gives it a
   working URL) OR by **pasting a public image URL that opens directly in a
   browser** (test the URL in a new tab first — the raw image must show).
4. **Activate** it → **Apply & Status → Apply signature to everyone**.
5. Send a test email → the banner should now appear.

## Required Coolify settings (so images work + persist)
- Persistent Storage volume mounted at **`/data`**.
- Env vars: `DATA_DIR=/data`, `PUBLIC_BASE_URL=https://signature.crownitsolution.com`,
  `APP_SECRET=<random>`.
- **Redeploy** after setting these (Force deploy if a normal redeploy shows no
  change) — some earlier UI changes only appear after a fresh deploy.

## Status
- Signature: working correctly for recipients.
- Banner: still broken because its image URL is unreachable; fix = re-create the
  banner from a real, public image (upload a PNG or a valid public URL).
- All app changes committed and pushed to GitHub (`dev-dialphone/Email-signature`).

## Key takeaway
A banner in email can only be a **plain hosted image** (`<img src="https://...">`).
Canvas/HTML-with-JavaScript designs and local file paths never render in email —
export to PNG and upload, or use a public image URL that opens on its own.
