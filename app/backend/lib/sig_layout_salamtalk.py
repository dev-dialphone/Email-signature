"""Salamtalk 'Accounts' hardcoded layout: a 6px blue left band, a large blue
department title, bold team/company lines, stacked contacts + address, the logo,
then a big outline-circle social row. Faithful to the supplied design but driven
by entity values so any entity can use it. Table + inline CSS = email safe.
Values arrive pre-escaped from build_signature_html."""
from .sig_layouts import SigVals

_BAND = "#20a8d8"     # left vertical band + icon ring
_TITLE = "#249ed0"    # department title blue
_LINK = "#2b9fd0"     # email/website link blue


def salamtalk_pro(v: SigVals) -> str:
    accent = v.accent or _BAND
    ring = accent
    title_blue = accent if v.accent else _TITLE
    contact_rows = "".join(
        f'<tr><td style="font-size:18px;line-height:28px;color:{v.text};padding:0;">{p}</td></tr>'
        for p in [v.phone, v.email_link, v.website_link] if p)
    address = (f'<tr><td style="padding-top:4px;font-size:18px;line-height:28px;color:{v.text};">{v.address}</td></tr>'
               if v.address else "")
    # Logo: use the real logo image when set (sized big); otherwise fall back to a
    # text wordmark + wifi arc like the original design.
    if v.logo_src:
        logo = (f'<img src="{v.logo_src}" alt="" style="display:block;max-width:260px;'
                f'max-height:90px;width:auto;height:auto;border:0;" />')
    else:
        logo = (
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
            f'<td style="font-size:48px;line-height:48px;font-weight:700;letter-spacing:-2px;color:#050505;">{v.company or v.name}</td>'
            f'<td style="padding-left:1px;padding-top:7px;vertical-align:middle;">'
            f'<span style="display:inline-block;width:13px;height:13px;border:4px solid {ring};'
            f'border-left-color:transparent;border-radius:50%;"></span></td></tr></table>'
        )
    inner = (
        f'<tr><td style="padding:0;font-size:30px;line-height:34px;font-weight:700;color:{title_blue};">{v.name}</td></tr>'
        + (f'<tr><td style="padding-top:2px;font-size:19px;line-height:24px;font-weight:700;color:#111111;">{v.title}</td></tr>' if v.title else '')
        + (f'<tr><td style="padding:0;font-size:19px;line-height:24px;font-weight:700;color:#111111;">{v.company}</td></tr>' if v.company else '')
        + (f'<tr><td style="padding-top:22px;">&nbsp;</td></tr>' if contact_rows else '')
        + contact_rows
        + address
        + f'<tr><td style="padding-top:26px;">{logo}</td></tr>'
        + (f'<tr><td style="padding-top:36px;padding-bottom:12px;">{v.social_html}</td></tr>' if v.social_html else '')
    )
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'style="width:650px;max-width:650px;border-collapse:collapse;'
        f'font-family:Arial,Helvetica,sans-serif;color:#111111;"><tr>'
        f'<td style="width:6px;background:{accent};font-size:0;line-height:0;">&nbsp;</td>'
        '<td style="padding:0 0 0 35px;vertical-align:top;">'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'style="border-collapse:collapse;width:100%;">{inner}</table></td></tr></table>'
    )


SALAMTALK_LAYOUTS = {"salamtalk_pro": salamtalk_pro}
