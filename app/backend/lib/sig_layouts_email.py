"""Full 'real email signature' layout (VestaCall style) — a bordered card with a
big logo column on the left, an iconised contact block on the right, a social
row, and a two-tile footer (support + website). NOT a business-card strip. Table
+ inline CSS = email safe. Values arrive pre-escaped from build_signature_html;
v.accent/v.text carry the entity theme."""
from .sig_layouts import SigVals


def _icon_row(glyph: str, value: str, accent: str, top: bool = False) -> str:
    """One contact line: a bordered rounded glyph tile + the value beside it."""
    if not value:
        return ""
    valign = "top" if top else "middle"
    return (
        '<tr>'
        f'<td width="38" valign="{valign}" style="width:38px;padding-bottom:9px;">'
        '<table cellpadding="0" cellspacing="0" border="0" width="30" height="30" '
        'style="width:30px;height:30px;border:1px solid #d7d7d7;border-radius:6px;">'
        f'<tr><td align="center" valign="middle" style="font-size:16px;color:{accent};'
        f'font-weight:bold;">{glyph}</td></tr></table></td>'
        f'<td valign="{valign}" style="padding-bottom:9px;font-family:Arial,sans-serif;'
        f'font-size:14px;line-height:20px;color:{v_text_holder[0]};">{value}</td></tr>'
    )


# _icon_row needs the entity text colour; stash it per-render (single-threaded
# request path). ponytail: module-level holder; pass text explicitly if this ever
# runs concurrently within one process.
v_text_holder = ["#222222"]


def professional(v: SigVals) -> str:
    accent = v.accent
    v_text_holder[0] = v.text
    # LEFT: big logo filling a bordered column (fit, never crop).
    logo = (
        f'<img src="{v.logo_src}" alt="" style="display:block;max-width:200px;'
        f'max-height:200px;width:auto;height:auto;margin:0 auto;border:0;'
        f'outline:none;text-decoration:none;" />' if v.logo_src else v.logo_html)

    contact_tbl = (
        '<table cellpadding="0" cellspacing="0" border="0" width="100%">'
        + _icon_row("&#9742;", v.phone, accent)
        + _icon_row("&#9993;", v.email_link, accent)
        + _icon_row("&#9678;", v.website_link, accent)
        + _icon_row("&#9679;", v.address, accent, top=True)
        + '</table>'
    )

    company_line = (f'<div style="font-family:Arial,sans-serif;font-size:15px;'
                    f'line-height:21px;color:{v.text};margin-top:2px;">{v.company}</div>'
                    if v.company else '')

    details = (
        f'<div style="font-family:Arial,sans-serif;font-size:22px;line-height:27px;'
        f'font-weight:700;color:#151515;">{v.name}</div>'
        + (f'<div style="font-family:Arial,sans-serif;font-size:16px;line-height:22px;'
           f'color:{accent};font-weight:500;margin-top:3px;">{v.title}</div>' if v.title else '')
        + company_line
        + f'<table cellpadding="0" cellspacing="0" border="0" style="margin:13px 0 15px 0;">'
          f'<tr><td width="48" height="3" style="width:48px;height:3px;background:{accent};'
          f'font-size:0;line-height:0;">&nbsp;</td></tr></table>'
        + contact_tbl
    )

    top = (
        '<tr>'
        f'<td width="205" valign="middle" style="width:205px;padding:12px;text-align:center;'
        f'border-right:1px solid #dddddd;">{logo}</td>'
        f'<td valign="middle" style="padding:24px 26px;">{details}</td>'
        '</tr>'
    )

    social = (
        '<tr><td colspan="2" style="padding:0 20px;">'
        f'<table cellpadding="0" cellspacing="0" border="0" width="100%"><tr>'
        f'<td height="2" style="height:2px;background:{accent};font-size:0;line-height:0;">'
        '&nbsp;</td></tr></table></td></tr>'
        '<tr><td colspan="2" align="center" style="padding:13px 15px 14px 15px;">'
        f'<div style="font-family:Arial,sans-serif;font-size:15px;line-height:20px;'
        f'color:{v.text};">Follow us on</div>'
        f'<div style="margin-top:9px;">{v.social_html}</div>'
        '</td></tr>'
    ) if v.social_html else ''

    footer = (
        '<tr><td colspan="2" style="padding:0;">'
        '<table cellpadding="0" cellspacing="0" border="0" width="100%"><tr>'
        # support tile (accent bg)
        f'<td width="52%" valign="middle" style="width:52%;background:{accent};'
        f'padding:18px 20px;color:#ffffff;">'
        '<table cellpadding="0" cellspacing="0" border="0"><tr>'
        '<td valign="middle" style="padding-right:12px;">'
        '<table cellpadding="0" cellspacing="0" border="0" width="48" height="48" '
        'style="width:48px;height:48px;border:2px solid #ffffff;border-radius:50%;">'
        '<tr><td align="center" valign="middle" style="font-size:24px;color:#ffffff;">'
        '&#9742;</td></tr></table></td>'
        '<td valign="middle">'
        '<div style="font-family:Arial,sans-serif;font-size:14px;line-height:19px;'
        'font-weight:700;">WE\'RE HERE TO HELP</div>'
        '<div style="font-family:Arial,sans-serif;font-size:12px;line-height:18px;'
        'margin-top:2px;">Reliable Support. Real People.</div></td></tr></table></td>'
        # website tile (dark bg)
        '<td width="48%" valign="middle" style="width:48%;background:#171719;'
        'padding:18px;color:#ffffff;">'
        '<table cellpadding="0" cellspacing="0" border="0"><tr>'
        '<td valign="middle" style="padding-right:12px;">'
        '<table cellpadding="0" cellspacing="0" border="0" width="42" height="42" '
        f'style="width:42px;height:42px;border:2px solid {accent};border-radius:50%;">'
        f'<tr><td align="center" valign="middle" style="font-size:21px;color:{accent};">'
        '&#9678;</td></tr></table></td>'
        '<td valign="middle">'
        '<div style="font-family:Arial,sans-serif;font-size:13px;line-height:18px;'
        'color:#ffffff;">Explore more</div>'
        f'{v.website_link or ""}</td></tr></table></td>'
        '</tr></table></td></tr>'
    )

    return (
        '<table cellpadding="0" cellspacing="0" border="0" width="600" '
        'style="width:600px;max-width:600px;border:1px solid #d9d9d9;border-radius:8px;'
        'border-collapse:separate;overflow:hidden;background:#ffffff;'
        f'font-family:Arial,sans-serif;color:{v.text};">'
        + top + social + footer + '</table>'
    )


EMAIL_LAYOUTS = {"professional": professional}
