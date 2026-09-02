"""Four extra professional layouts so different entities look genuinely
distinct in structure (not just colour). All table-based + inline CSS = email
safe. Values arrive pre-escaped/pre-styled from build_signature_html; v.accent
and v.text carry the entity's theme colours."""
from .sig_layouts import SigVals


def _contacts(v: SigVals, sep: str = "<br>") -> str:
    return sep.join(p for p in [v.phone, v.email_link, v.website_link, v.address] if p)


def sidebar(v: SigVals) -> str:
    """Left accent sidebar (coloured vertical band) | name/title/contacts, logo
    top-right. Corporate, structured — reads clearly different from classic."""
    left = (
        '<table cellpadding="0" cellspacing="0" border="0">'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:19px;font-weight:bold;color:{v.accent};padding-bottom:2px;">{v.name}</td></tr>'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:13px;padding-bottom:2px;">{v.title}</td></tr>'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:13px;font-weight:bold;color:{v.text};padding-bottom:8px;">{v.company}</td></tr>'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:13px;color:{v.text};line-height:1.6;">{_contacts(v)}</td></tr>'
        f'<tr><td style="padding-top:10px;">{v.social_html}</td></tr></table>'
    )
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;"><tr>'
        f'<td width="6" style="background:{v.accent};border-radius:3px;">&nbsp;</td>'
        f'<td valign="top" style="padding:0 20px;">{left}</td>'
        f'<td valign="top" align="right">{v.logo_html}</td>'
        '</tr></table>'
    )


def banner_top(v: SigVals) -> str:
    """Logo + name on a top row above a full-width accent divider, contacts as a
    single centred line below, social centred. Clean, modern, magazine-like."""
    parts = " &nbsp;|&nbsp; ".join(p for p in [v.phone, v.email_link, v.website_link] if p)
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;">'
        f'<tr><td valign="middle" style="padding-bottom:8px;">{v.logo_html}</td>'
        f'<td valign="middle" align="right" style="padding-bottom:8px;">'
        f'<div style="font-family:Arial,sans-serif;font-size:19px;font-weight:bold;color:{v.accent};">{v.name}</div>'
        f'<div style="font-family:Arial,sans-serif;font-size:13px;">{v.title}</div>'
        f'<div style="font-family:Arial,sans-serif;font-size:13px;font-weight:bold;color:{v.text};">{v.company}</div></td></tr>'
        f'<tr><td colspan="2" style="padding:6px 0;"><div style="height:2px;background:{v.accent};"></div></td></tr>'
        f'<tr><td colspan="2" align="center" style="font-family:Arial,sans-serif;font-size:13px;color:{v.text};padding:4px 0;">{parts}</td></tr>'
        + (f'<tr><td colspan="2" align="center" style="font-family:Arial,sans-serif;font-size:12px;color:{v.text};padding-bottom:6px;">{v.address}</td></tr>' if v.address else '')
        + f'<tr><td colspan="2" align="center">{v.social_html}</td></tr></table>'
    )


def elegant(v: SigVals) -> str:
    """Centred, serif-flavoured, generous spacing — a premium/executive feel.
    Logo centred on top, thin accent rule, name in caps."""
    contacts = " &nbsp;&middot;&nbsp; ".join(p for p in [v.phone, v.email_link, v.website_link] if p)
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;text-align:center;">'
        + (f'<tr><td style="padding-bottom:8px;" align="center">{v.logo_html}</td></tr>' if v.logo_html else '')
        + f'<tr><td align="center" style="font-family:Georgia,\'Times New Roman\',serif;font-size:20px;font-weight:bold;letter-spacing:1px;color:{v.accent};text-transform:uppercase;">{v.name}</td></tr>'
        f'<tr><td align="center" style="font-family:Georgia,serif;font-size:13px;font-style:italic;padding-bottom:4px;">{v.title}</td></tr>'
        f'<tr><td align="center" style="padding:6px 0;"><div style="width:60px;height:2px;background:{v.accent};margin:0 auto;"></div></td></tr>'
        f'<tr><td align="center" style="font-family:Arial,sans-serif;font-size:13px;font-weight:bold;color:{v.text};">{v.company}</td></tr>'
        f'<tr><td align="center" style="font-family:Arial,sans-serif;font-size:13px;color:{v.text};padding:2px 0 6px;">{contacts}</td></tr>'
        + (f'<tr><td align="center" style="font-family:Arial,sans-serif;font-size:12px;color:{v.text};padding-bottom:6px;">{v.address}</td></tr>' if v.address else '')
        + f'<tr><td align="center">{v.social_html}</td></tr></table>'
    )


def card(v: SigVals) -> str:
    """Bordered 'business card' box with an accent header bar. Distinct framed
    look — clearly a different brand system from the open layouts."""
    inner = (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:100%;"><tr>'
        f'<td valign="top">'
        f'<div style="font-family:Arial,sans-serif;font-size:18px;font-weight:bold;color:{v.accent};">{v.name}</div>'
        f'<div style="font-family:Arial,sans-serif;font-size:13px;padding-bottom:2px;">{v.title}</div>'
        f'<div style="font-family:Arial,sans-serif;font-size:13px;font-weight:bold;color:{v.text};padding-bottom:8px;">{v.company}</div>'
        f'<div style="font-family:Arial,sans-serif;font-size:13px;color:{v.text};line-height:1.6;">{_contacts(v)}</div>'
        f'<div style="padding-top:10px;">{v.social_html}</div></td>'
        f'<td valign="top" align="right" style="padding-left:16px;">{v.logo_html}</td>'
        '</tr></table>'
    )
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;border:1px solid #e2e2e2;border-radius:8px;">'
        f'<tr><td style="height:6px;background:{v.accent};border-radius:8px 8px 0 0;font-size:0;line-height:0;">&nbsp;</td></tr>'
        f'<tr><td style="padding:16px 18px;">{inner}</td></tr></table>'
    )


def _round_img(src: str, size: int = 120) -> str:
    # Round image via border-radius (widely supported in Gmail/Apple Mail;
    # degrades to a square in the few clients that ignore it).
    if not src:
        return ""
    return (f'<img src="{src}" width="{size}" height="{size}" alt="" '
            f'style="width:{size}px;height:{size}px;border-radius:{size//2}px;'
            f'object-fit:cover;display:block;border:0;" />')


def photo_circle(v: SigVals) -> str:
    """Round photo/logo on the left, a thin accent divider, then name (large),
    coloured title, contacts and small round social icons on the right."""
    contacts = "<br>".join(p for p in [v.phone, v.email_link, v.website_link] if p)
    right = (
        f'<div style="font-family:Arial,sans-serif;font-size:22px;font-weight:bold;color:{v.text};">{v.name}</div>'
        f'<div style="font-family:Arial,sans-serif;font-size:13px;font-weight:bold;color:{v.accent};padding-bottom:6px;">{v.title}</div>'
        f'<div style="font-family:Arial,sans-serif;font-size:13px;color:{v.text};line-height:1.6;">{contacts}</div>'
        f'<div style="padding-top:8px;">{v.social_html}</div>'
    )
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;"><tr>'
        f'<td valign="middle" width="130">{_round_img(v.logo_src, 120)}</td>'
        f'<td width="1" style="background:#dddddd;">&nbsp;</td>'
        f'<td valign="middle" style="padding-left:20px;">{right}</td>'
        '</tr></table>'
    )


def banner_hex(v: SigVals) -> str:
    """Horizontal banner: brand/logo block on a teal panel (left), a framed
    photo/logo in the centre, name + icon-bulleted contacts on the right.
    (True hexagon clipping isn't email-safe, so the centre image is round.)"""
    accent = v.accent
    left = (
        f'<div style="font-family:Arial,sans-serif;font-size:16px;font-weight:bold;color:#ffffff;">{v.company or "BRAND NAME"}</div>'
        + (f'<div style="font-family:Arial,sans-serif;font-size:11px;color:#e6f2f2;padding-bottom:8px;">{v.title}</div>' if v.title else '')
        + f'<div style="padding-top:8px;">{v.social_html}</div>'
    )
    contact_rows = "".join(
        f'<tr><td style="font-family:Arial,sans-serif;font-size:12px;color:{v.text};padding:3px 0;">{p}</td></tr>'
        for p in [v.phone, v.email_link, v.website_link, v.address] if p)
    right = (
        f'<div style="font-family:Arial,sans-serif;font-size:18px;font-weight:bold;color:{accent};">{v.name}</div>'
        f'<div style="font-family:Arial,sans-serif;font-size:12px;font-weight:bold;color:{v.text};padding-bottom:6px;">{v.title}</div>'
        f'<table cellpadding="0" cellspacing="0" border="0">{contact_rows}</table>'
    )
    return (
        '<table cellpadding="0" cellspacing="0" border="0" style="width:600px;border:1px solid #e2e2e2;"><tr>'
        f'<td valign="middle" width="150" style="background:{accent};padding:16px;">{left}</td>'
        f'<td valign="middle" width="140" align="center" style="padding:10px;">{_round_img(v.logo_src, 110)}</td>'
        f'<td valign="middle" style="padding:12px 16px;">{right}</td>'
        '</tr></table>'
    )


PRO_LAYOUTS = {"sidebar": sidebar, "banner_top": banner_top,
               "elegant": elegant, "card": card,
               "photo_circle": photo_circle, "banner_hex": banner_hex}
