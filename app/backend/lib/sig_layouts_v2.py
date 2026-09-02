"""Structurally DISTINCT signature layouts (2026 trends) — not just repositioned
columns. cta_button = single column + real pill CTA; qr_card = scan-for-vCard QR;
promo_banner = full-width marketing/GIF banner strip; dark = inverted dark-mode.
Table + inline CSS = email safe. Values arrive pre-escaped from
build_signature_html; cta_url/qr_src are derived there."""
from .sig_layouts import SigVals


def _contacts_br(v: SigVals) -> str:
    return "<br>".join(p for p in [v.phone, v.email_link, v.website_link, v.address] if p)


def cta_button(v: SigVals) -> str:
    """True single column with a solid accent PILL button (Book a call). Research:
    single-column + one button CTA outperforms multi-column ~3x on clicks."""
    label = v.cta_label or "Book a call"
    btn = (
        f'<a href="{v.cta_url}" target="_blank" rel="noopener noreferrer" '
        f'style="display:inline-block;padding:10px 22px;background:{v.accent};color:#ffffff;'
        f'font-family:Arial,sans-serif;font-size:13px;font-weight:bold;text-decoration:none;'
        f'border-radius:6px;">{label}</a>'
    ) if v.cta_url else ""
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:340px;">'
        + (f'<tr><td style="padding-bottom:8px;">{v.logo_html}</td></tr>' if v.logo_html else '')
        + f'<tr><td style="font-family:Arial,sans-serif;font-size:19px;font-weight:bold;color:{v.accent};">{v.name}</td></tr>'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:13px;padding-bottom:2px;">{v.title}</td></tr>'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:13px;font-weight:bold;color:{v.text};padding-bottom:8px;">{v.company}</td></tr>'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:13px;color:{v.text};line-height:1.6;">{_contacts_br(v)}</td></tr>'
        + (f'<tr><td style="padding:12px 0 10px;">{btn}</td></tr>' if btn else '<tr><td style="padding-top:10px;"></td></tr>')
        + f'<tr><td>{v.social_html}</td></tr></table>'
    )


def qr_card(v: SigVals) -> str:
    """Bordered card: identity on the left, a QR block on the right with a caption.
    Instantly recognisable vs every text-only layout."""
    left = (
        f'<div style="font-family:Arial,sans-serif;font-size:18px;font-weight:bold;color:{v.accent};">{v.name}</div>'
        f'<div style="font-family:Arial,sans-serif;font-size:13px;padding-bottom:2px;">{v.title}</div>'
        f'<div style="font-family:Arial,sans-serif;font-size:13px;font-weight:bold;color:{v.text};padding-bottom:8px;">{v.company}</div>'
        f'<div style="font-family:Arial,sans-serif;font-size:13px;color:{v.text};line-height:1.6;">{_contacts_br(v)}</div>'
        f'<div style="padding-top:10px;">{v.social_html}</div>'
    )
    qr = (
        f'<img src="{v.qr_src}" width="104" height="104" alt="QR" style="display:block;border:0;" />'
        f'<div style="font-family:Arial,sans-serif;font-size:11px;color:{v.text};padding-top:4px;text-align:center;">Scan to connect</div>'
    ) if v.qr_src else v.logo_html
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;border:1px solid #e2e2e2;border-radius:8px;">'
        f'<tr><td valign="top" style="padding:18px;">{left}</td>'
        f'<td valign="middle" width="130" align="center" style="padding:18px;border-left:1px solid #eee;">{qr}</td>'
        '</tr></table>'
    )


def promo_banner(v: SigVals) -> str:
    """Full-width brand/GIF banner strip on top, one-line identity + contacts under
    it. Marketing feel, structurally unlike the identity-first layouts."""
    banner = (
        f'<img src="{v.logo_src}" alt="" style="display:block;width:600px;max-width:600px;'
        f'height:auto;border:0;" />' if v.logo_src else "")
    idline = " &middot; ".join(p for p in [f'<strong style="color:{v.accent};">{v.name}</strong>', v.title, v.company] if p)
    contacts = " &nbsp;|&nbsp; ".join(p for p in [v.phone, v.email_link, v.website_link] if p)
    tagline = (f'<tr><td style="font-family:Arial,sans-serif;font-size:13px;font-style:italic;color:{v.text};padding-bottom:6px;">{v.tagline}</td></tr>'
               if v.tagline else "")
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;">'
        + (f'<tr><td style="padding-bottom:10px;">{banner}</td></tr>' if banner else '')
        + f'<tr><td style="height:3px;background:{v.accent};font-size:0;line-height:0;">&nbsp;</td></tr>'
        + f'<tr><td style="font-family:Arial,sans-serif;font-size:14px;color:{v.text};padding:8px 0 2px;">{idline}</td></tr>'
        + tagline
        + f'<tr><td style="font-family:Arial,sans-serif;font-size:13px;color:{v.text};padding-bottom:8px;">{contacts}</td></tr>'
        + f'<tr><td>{v.social_html}</td></tr></table>'
    )


def dark(v: SigVals) -> str:
    """Inverted dark-mode block: dark bg, light text, accent name + pill. 2026
    dark-mode-first trend; none of the other layouts invert."""
    label = v.cta_label or "Book a call"
    btn = (
        f'<a href="{v.cta_url}" target="_blank" rel="noopener noreferrer" '
        f'style="display:inline-block;padding:8px 18px;background:{v.accent};color:#111111;'
        f'font-family:Arial,sans-serif;font-size:12px;font-weight:bold;text-decoration:none;'
        f'border-radius:6px;">{label}</a>' if v.cta_url else "")
    inner = (
        f'<tr><td style="font-family:Arial,sans-serif;font-size:19px;font-weight:bold;color:{v.accent};">{v.name}</td></tr>'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:13px;color:#dddddd;padding-bottom:2px;">{v.title}</td></tr>'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:13px;font-weight:bold;color:#ffffff;padding-bottom:8px;">{v.company}</td></tr>'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:13px;color:#cccccc;line-height:1.6;">{_contacts_br(v)}</td></tr>'
        + (f'<tr><td style="padding:12px 0 8px;">{btn}</td></tr>' if btn else '<tr><td style="padding-top:8px;"></td></tr>')
        + f'<tr><td>{v.social_html}</td></tr>'
    )
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;background:#111111;border-radius:8px;">'
        f'<tr><td style="padding:20px 22px;"><table cellpadding="0" cellspacing="0" border="0">{inner}</table></td></tr></table>'
    )


V2_LAYOUTS = {"cta_button": cta_button, "qr_card": qr_card,
              "promo_banner": promo_banner, "dark": dark}
