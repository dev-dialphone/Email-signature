"""Derive CTA link + QR image for the v2 layouts without any schema change.
ponytail: CTA is website-derived and the QR uses a public image service
(api.qrserver.com); promote to real editable cta_url/qr_data fields later."""
from urllib.parse import quote


def derive_cta_qr(website: str, email: str) -> tuple[str, str]:
    """Returns (cta_url, qr_src). CTA prefers the website, else a mailto; the QR
    encodes the same target via a public QR image endpoint."""
    cta_url = website or (f"mailto:{email}" if email else "")
    target = website or (f"mailto:{email}" if email else "")
    qr_src = (f"https://api.qrserver.com/v1/create-qr-code/?size=104x104&data={quote(target, safe='')}"
              if target else "")
    return cta_url, qr_src
