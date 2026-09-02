# Implementation Plan — Genuinely Distinct Signature Templates

## Problem
The 14 existing layouts (`classic, modern, minimal, bold, compact, stacked,
stacked_social_bottom, arranged, sidebar, banner_top, elegant, card,
photo_circle, banner_hex`) are all the **same idea**: name + logo + contacts +
social icons arranged in 1–2 table columns with an accent colour. They differ in
*position*, not in *structure or content model*. To a viewer they read alike.

## What the research says is actually different (2026 signature trends)
Sources at the bottom. The high-signal, currently-**missing** patterns:

1. **Single-column + CTA button** — one narrow column, a real coloured
   "Book a call / Schedule a meeting" pill button. Research: single-column beats
   two-column CTR ~3×; a button CTA is the dominant modern element. *We have zero
   button-based layouts.*
2. **QR-code layout** — signature with a QR block (links to vCard / booking).
   Visually unmistakable vs everything we have.
3. **Promo / GIF banner strip** — a full-width brand banner image row (event,
   product, or animated GIF) above/below the identity block. Distinct "marketing"
   feel. Uses the logo image slot as the banner for now.
4. **Vertical band + headshot tile** — coloured full-height left panel with the
   logo/photo *inside* it (reversed-out), identity on white to the right. Reads
   as a "brand card", structurally unlike our thin 6px `sidebar` strip.
5. **Dark-mode signature** — dark background block, light text, accent glow.
   Research flags dark-mode as a 2026 default. None of ours invert.

Pick the 3 most distinct to ship first: **cta_button, qr_card, promo_banner**.
`vband_photo` and `dark` are stretch (same effort, listed for completeness).

## Constraints (must honor)
- Email-safe: table layout + inline CSS only, ~600px wide. No `<style>`, no flex.
- 150-line file cap (doctrine). New file `sig_layouts_v2.py`, registered via the
  Open/Closed extension point — do **not** edit `sig_layouts.py` beyond one
  import line in `_register_extra()`.
- Values arrive **pre-escaped** in `SigVals`; never re-escape.
- Layout exclusivity already enforced in `api.py` — no change needed.

## Data available vs. new data needed
`SigVals` already carries name/title/company/phone/email/address/website/logo/
social/accent/text/logo_src. Enough for `promo_banner` and `vband_photo` and
`dark` with **zero schema changes**.

`cta_button` and `qr_card` need one new value each:
- `cta_url` + `cta_label` (button) — e.g. a Calendly/Cal.com link.
- `qr_src` (QR image URL) — or auto-generate from a URL.

Two options:
- **(A) No-schema MVP** — derive CTA from existing `website`/`email` (mailto or
  site) and generate the QR image on the fly from `website` using a public QR
  image endpoint (`api.qrserver.com/v1/create-qr-code/?data=...`). Ships today,
  no migration. `ponytail:` external QR service; swap for a local generator later.
- **(B) Proper fields** — add `cta_url`, `cta_label`, `qr_data` to the `sig`
  table + `SigUpdate` model + `DESIGN_FIELDS`/persisted-fields lists + frontend
  inputs. Cleaner, but touches db/api/frontend.

Recommend **(A) for this pass** to keep the change surgical; note (B) as upgrade.

## Files to change
1. **NEW** `app/backend/lib/sig_layouts_v2.py` (<150 lines) — the new layout fns:
   `cta_button`, `qr_card`, `promo_banner` (+ optional `vband_photo`, `dark`).
   Imports `SigVals` from `sig_layouts`. Add a `V2_LAYOUTS` dict at the bottom.
2. `app/backend/lib/sig_layouts.py` — in `_register_extra()`, add
   `from .sig_layouts_v2 import V2_LAYOUTS` and `**V2_LAYOUTS` to the return.
   (One import + one spread. Registry stays open/closed.)
3. `app/backend/lib/email_signature.py` — only if we add a `qr_src`/`cta`:
   compute them in `build_signature_html` and pass into `SigVals`. For option (A),
   derive `qr_src` from `website` and `cta` from `website`/booking here. Add the
   three fields to the `SigVals` dataclass (`sig_layouts.py`) with defaults so
   older layouts ignore them.
4. `app/frontend/app.js` — append the new tiles to the `LAYOUTS` array (id,
   label, one-line description) so they appear in the Design picker.
5. `tests/` — add a render smoke test per new layout (asserts key markers:
   button href, `qrserver`, banner `<img>`), mirroring existing layout tests.

## SigVals additions (option A, backward-safe)
```python
# sig_layouts.py, in @dataclass SigVals (all default to "")
cta_url: str = ""     # booking/scheduling link (full URL)
cta_label: str = ""   # e.g. "Book a call"
qr_src: str = ""      # QR image URL (generated from website in email_signature)
tagline: str = ""     # already-collected but unused; nice for promo_banner
```
Existing layouts don't reference these → no behavioural change.

## New layout sketches (structure only)
- **cta_button** — single left-aligned column: logo (small) → name/title/company
  → contacts stacked → a `<a>` styled as a solid accent pill
  (`display:inline-block;padding:10px 22px;border-radius:6px;background:accent;
  color:#fff;`) → social row. Distinct because of the button + true single column.
- **qr_card** — two cells: left = identity block; right = QR `<img>` (110px) with
  a tiny "Scan for vCard / book time" caption under it. Bordered card frame.
- **promo_banner** — row 1: full-width banner `<img>` (the logo_src stretched, or
  a dedicated banner later) → row 2: name·title·company one line → row 3:
  contacts + social. Marketing-strip feel.
- **vband_photo** (stretch) — table with a wide coloured left `<td>` (accent bg,
  ~150px) holding the logo reversed-out + tagline in white; right `<td>` white
  with identity/contacts. Full-height brand panel.
- **dark** (stretch) — outer `<td>` with `background:#111;` , light text
  (`#eee`), accent used for name + button; social icons `plain` style.

## Test / verify plan
- `pytest tests/ -k layout` (or the existing signature test target) — new layouts
  render without error and contain their signature markers.
- Manual: run the app, open Design tab, click each new tile, confirm the
  `/signature/preview` HTML shows the button/QR/banner. Use `preview_start`.
- Litmus: paste one rendered signature into Gmail compose to eyeball email-client
  rendering (button + QR are the risky ones).

## Rollout order
1. Add SigVals fields (safe, no-op for old layouts).
2. Write `sig_layouts_v2.py` with the 3 core layouts + `V2_LAYOUTS`.
3. Wire QR/CTA derivation in `email_signature.py` (option A).
4. Register in `_register_extra()`.
5. Add frontend tiles.
6. Tests + manual preview.
7. (Later, option B) promote CTA/QR/banner to real editable fields.

## Sources
- https://www.bybrand.io/blog/trends-email-signatures/
- https://www.crossware365.com/blog/email-signature-design-trends-for-2026-whats-in-and-whats-out
- https://bulksignature.com/blog/email-signature-design-trends
- https://wavecnct.com/blogs/email-signature-best-practices-2026
- https://www.wisestamp.com/examples/cool-email-signatures/
- https://stripo.email/blog/how-to-create-an-eye-catching-gif-email-signature/
