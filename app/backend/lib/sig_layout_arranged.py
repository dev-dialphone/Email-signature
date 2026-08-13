"""The "arranged" signature layout: admin picks WHERE the logo and the social
group sit, independently, and it renders as email-safe <table> HTML (no
position:absolute, which Gmail/Outlook strip). Saved positions are applied
verbatim at send time.

logo_pos:   right | below
social_pos: with_name | below_logo | bottom
"""
from .sig_layouts import SigVals, _row


def _contact_table(v: SigVals) -> str:
    return (
        '<table cellpadding="0" cellspacing="0" border="0">'
        f'<tr><td style="font-family:Arial,sans-serif;font-size:20px;font-weight:bold;color:{v.accent};padding-bottom:2px;">{v.name}</td></tr>'
        + _row(v.title, v.muted, 13)
        + _row(f'<strong>{v.company}</strong>', v.text, 13)
        + '<tr><td style="padding:6px 0 5px;"><div style="border-top:1px solid #ddd;"></div></td></tr>'
        + _row(v.phone, v.text) + _row(v.email_link, v.text)
        + _row(v.address, v.muted) + _row(v.website_link, v.text)
        + '</table>'
    )


def _logo_cell(v: SigVals, extra: str = "") -> str:
    return f'<td valign="top" align="right" style="padding-left:24px;{extra}">{v.logo_html}</td>' if v.logo_html else ""


def arranged(v: SigVals) -> str:
    """Compose the four rows from the two independent position choices."""
    social = v.social_html
    # Socials can occupy the top-right slot only when the logo isn't already there.
    social_with_name = social and v.social_pos == "with_name" and v.logo_pos != "right"
    # Row 1: contact left; top-right holds the logo (logo_pos=right) or the socials
    # (social_pos=with_name and the logo is elsewhere).
    if v.logo_pos == "right":
        top_right = _logo_cell(v)
    elif social_with_name:
        top_right = f'<td valign="top" align="right">{social}</td>'
    else:
        top_right = ""
    row_top = f'<tr><td valign="top">{_contact_table(v)}</td>{top_right}</tr>'

    tail = ""
    # Logo below (full-width row) when logo_pos=below.
    if v.logo_pos == "below" and v.logo_html:
        tail += f'<tr><td colspan="2" style="padding-top:10px;">{v.logo_html}</td></tr>'
    # Socials render below unless they already took the top-right slot. This also
    # covers with_name when the logo occupies the right (socials can't vanish).
    if social and not social_with_name:
        tail += f'<tr><td colspan="2" style="padding-top:10px;">{social}</td></tr>'

    return ('<table cellpadding="0" cellspacing="0" border="0" style="width:600px;">'
            + row_top + tail + '</table>')
