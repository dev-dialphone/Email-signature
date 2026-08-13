"""Extra single-column signature layouts (kept out of sig_layouts.py for the
150-line cap). Both put the company logo inline at the bottom; they differ only
in where the social icons sit."""
from .sig_layouts import SigVals


def _line(v: SigVals, label: str, value: str) -> str:
    if not value:
        return ""
    lbl = f'<strong style="color:{v.text};">{label}:</strong> ' if label else ""
    return f'<tr><td style="padding:2px 0;font-family:Arial,sans-serif;font-size:13px;color:{v.text};">{lbl}{value}</td></tr>'


def _company_addr(v: SigVals) -> str:
    parts = [f'<strong style="color:{v.text};">{v.company}</strong>' if v.company else "", v.address]
    joined = " &middot; ".join(p for p in parts if p)
    return f'<tr><td style="padding:2px 0;font-family:Arial,sans-serif;font-size:13px;color:{v.text};">{joined}</td></tr>' if joined else ""


def _contact_block(v: SigVals) -> str:
    return (
        '<table cellpadding="0" cellspacing="0" border="0">'
        + _line(v, "Phone", v.phone) + _line(v, "Email", v.email_link) + _company_addr(v)
        + '</table>'
    )


def _website_row(v: SigVals) -> str:
    return f'<tr><td colspan="2" style="padding-top:6px;font-weight:bold;">{v.website_link}</td></tr>' if v.website_link else ""


def _name_title(v: SigVals) -> str:
    return (
        f'<div style="font-family:Arial,sans-serif;font-size:22px;font-weight:bold;color:{v.accent};">{v.name}</div>'
        f'<div style="font-family:Arial,sans-serif;font-size:14px;color:{v.muted};padding-top:2px;">{v.title}</div>'
    )


def stacked(v: SigVals) -> str:
    """Name+title with socials on the right; logo inline at the bottom."""
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;">'
        f'<tr><td valign="top">{_name_title(v)}</td>'
        f'<td valign="middle" align="right">{v.social_html}</td></tr>'
        '<tr><td colspan="2" style="padding:8px 0;"><div style="border-top:1px solid #ddd;"></div></td></tr>'
        f'<tr><td colspan="2">{_contact_block(v)}</td></tr>'
        + _website_row(v)
        + (f'<tr><td colspan="2" style="padding-top:6px;">{v.logo_html}</td></tr>' if v.logo_html else '')
        + '</table>'
    )


def stacked_social_bottom(v: SigVals) -> str:
    """No socials by the name; socials sit at the very bottom, under the logo."""
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;">'
        f'<tr><td>{_name_title(v)}</td></tr>'
        '<tr><td style="padding:8px 0;"><div style="border-top:1px solid #ddd;"></div></td></tr>'
        f'<tr><td>{_contact_block(v)}</td></tr>'
        + (f'<tr><td style="padding-top:6px;font-weight:bold;">{v.website_link}</td></tr>' if v.website_link else '')
        + (f'<tr><td style="padding-top:6px;">{v.logo_html}</td></tr>' if v.logo_html else '')
        + (f'<tr><td style="padding-top:6px;">{v.social_html}</td></tr>' if v.social_html else '')
        + '</table>'
    )
