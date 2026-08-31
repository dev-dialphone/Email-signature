"""Server-side signature layouts — the SAME 6 templates the admin previews in
the design section, so the chosen layout is what actually gets sent to every
agent's recipients. Values arrive pre-escaped from build_signature_html."""
from dataclasses import dataclass

# Logo prominence — WIDTH in px (brand logos are usually wide, so width drives
# the size; height auto-scales). "large" is the default (bold, standout).
LOGO_SIZES = {"small": 120, "medium": 180, "large": 240}


@dataclass
class SigVals:
    name: str
    title: str
    company: str
    phone: str
    email_link: str      # full <a> mailto or ""
    address: str
    website_link: str    # full <a> or ""
    logo_html: str       # full <img> already sized, or ""
    social_html: str     # full social row table or ""
    accent: str = "#000000"
    text: str = "#333333"
    muted: str = "#888888"
    logo_pos: str = "right"          # right | below   (arranged layout)
    social_pos: str = "below_logo"   # with_name | below_logo | bottom


def _row(value: str, color: str, size: int = 13) -> str:
    if not value:
        return ""
    return f'<tr><td style="padding:2px 0;font-family:Arial,sans-serif;font-size:{size}px;color:{color};">{value}</td></tr>'


def classic(v: SigVals) -> str:
    left = (
        '<table cellpadding="0" cellspacing="0" border="0">'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:20px;font-weight:bold;color:{v.accent};padding-bottom:2px;">{v.name}</td></tr>'
        + _row(v.title, v.muted, 13)
        + _row(f'<strong>{v.company}</strong>', v.text, 13)
        + '<tr><td style="padding:6px 0 5px;"><div style="border-top:1px solid #ddd;"></div></td></tr>'
        + _row(v.phone, v.text) + _row(v.email_link, v.text)
        + _row(v.address, v.muted) + _row(v.website_link, v.text)
        + '</table>'
    )
    right = f'<table cellpadding="0" cellspacing="0" border="0"><tr><td align="right">{v.logo_html}</td></tr><tr><td align="right" style="padding-top:10px;">{v.social_html}</td></tr></table>'
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;">'
        f'<tr><td valign="top">{left}</td>'
        f'<td valign="top" align="right" style="padding-left:24px;">{right}</td></tr></table>'
    )


def modern(v: SigVals) -> str:
    parts = " &middot; ".join(p for p in [v.phone, v.email_link, v.website_link, v.address] if p)
    company_line = (f'<div style="font-family:Arial,sans-serif;font-size:13px;font-weight:bold;'
                    f'color:{v.text};">{v.company}</div>' if v.company else '')
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;">'
        f'<tr><td valign="middle" style="padding-bottom:10px;">{v.logo_html}</td>'
        f'<td valign="middle" style="padding-left:20px;padding-bottom:10px;">'
        f'<div style="font-family:Arial,sans-serif;font-size:18px;font-weight:bold;color:{v.accent};">{v.name}</div>'
        f'<div style="font-family:Arial,sans-serif;font-size:13px;color:{v.muted};">{v.title}</div>{company_line}</td></tr>'
        f'<tr><td colspan="2" style="padding-bottom:10px;"><div style="height:3px;background:{v.accent};"></div></td></tr>'
        f'<tr><td colspan="2" style="font-family:Arial,sans-serif;font-size:13px;color:{v.text};padding-bottom:10px;">{parts}</td></tr>'
        f'<tr><td colspan="2">{v.social_html}</td></tr></table>'
    )


def minimal(v: SigVals) -> str:
    contact = "&nbsp;&nbsp;".join(p for p in [v.phone, v.email_link] if p)
    left = (
        '<table cellpadding="0" cellspacing="0" border="0">'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:18px;font-weight:bold;color:{v.accent};padding-right:10px;">{v.name}</td>'
        f'<td style="font-family:Arial,sans-serif;font-size:13px;color:{v.muted};border-left:1px solid #ddd;padding-left:10px;">{v.title}</td></tr>'
        '<tr><td colspan="2" style="padding:6px 0 5px;"><div style="border-top:1px solid #eee;"></div></td></tr>'
        + (f'<tr><td colspan="2" style="font-family:Arial,sans-serif;font-size:13px;color:{v.text};padding-bottom:3px;">{contact}</td></tr>' if contact else '')
        + (f'<tr><td colspan="2" style="padding-bottom:5px;">{v.website_link}</td></tr>' if v.website_link else '')
        + f'<tr><td colspan="2" style="padding-top:5px;">{v.social_html}</td></tr></table>'
    )
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;">'
        f'<tr><td valign="top">{left}</td>'
        f'<td valign="top" align="right" style="padding-left:24px;">{v.logo_html}</td></tr></table>'
    )


def bold(v: SigVals) -> str:
    content = (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:100%;">'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:20px;font-weight:bold;color:{v.accent};padding-bottom:2px;">{v.name}</td>'
        f'<td rowspan="5" valign="top" align="right" style="padding-left:24px;">{v.logo_html}</td></tr>'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:13px;color:{v.muted};">{v.title}</td></tr>'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:13px;font-weight:bold;color:{v.text};padding-bottom:6px;">{v.company}</td></tr>'
        '<tr><td style="padding-bottom:6px;"><div style="border-top:1px solid #ddd;"></div></td></tr>'
        f'<tr><td><table cellpadding="0" cellspacing="0">{_row(v.phone, v.text)}{_row(v.email_link, v.text)}{_row(v.address, v.muted)}{_row(v.website_link, v.text)}</table></td></tr>'
        f'<tr><td style="padding-top:10px;">{v.social_html}</td></tr></table>'
    )
    return f'<table cellpadding="0" cellspacing="0" border="0" style="width:600px;"><tr><td style="border-left:5px solid {v.accent};padding-left:16px;">{content}</td></tr></table>'


def compact(v: SigVals) -> str:
    line1 = " &middot; ".join(p for p in [f'<strong>{v.name}</strong>', v.title] if p)
    line2 = " &middot; ".join(p for p in [v.phone, v.email_link, v.website_link] if p)
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;">'
        f'<tr><td colspan="2" style="font-family:Arial,sans-serif;font-size:14px;color:{v.text};padding-bottom:3px;">{line1}</td></tr>'
        + (f'<tr><td colspan="2" style="font-family:Arial,sans-serif;font-size:13px;color:{v.text};padding-bottom:6px;">{line2}</td></tr>' if line2 else '')
        + f'<tr><td valign="middle">{v.social_html}</td><td valign="middle" align="right">{v.logo_html}</td></tr></table>'
    )


def _register_extra() -> dict:
    # Imported lazily to avoid a circular import (extra imports SigVals from here).
    from .sig_layouts_extra import stacked, stacked_social_bottom
    from .sig_layout_arranged import arranged
    return {"stacked": stacked, "stacked_social_bottom": stacked_social_bottom,
            "arranged": arranged}


LAYOUTS = {"classic": classic, "modern": modern, "minimal": minimal,
           "bold": bold, "compact": compact, **_register_extra()}


def render_layout(layout_id: str, v: SigVals) -> str:
    return LAYOUTS.get(layout_id, classic)(v)
