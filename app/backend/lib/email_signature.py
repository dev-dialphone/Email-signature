"""Render an entity's signature template with a single user's own values.
Ported from the extracted module; the `settings.PUBLIC_BASE_URL` dependency is
replaced by a plain base_url argument (standalone app has no global settings)."""
from html import escape
from .sig_layouts import SigVals, LOGO_SIZES, render_layout


def _absolute_url(url: str, base_url: str | None = None) -> str:
    if url.startswith("/"):
        origin = (base_url or "").rstrip("/")
        if origin:
            return origin + url
    return url


_SOCIAL = {
    "facebook":  {"bg": "#1877F2", "icon": "https://img.icons8.com/ios-filled/50/ffffff/facebook-new.png"},
    "twitter":   {"bg": "#000000", "icon": "https://img.icons8.com/ios-filled/50/ffffff/twitterx.png"},
    "youtube":   {"bg": "#FF0000", "icon": "https://img.icons8.com/ios-filled/50/ffffff/youtube-play.png"},
    "linkedin":  {"bg": "#0A66C2", "icon": "https://img.icons8.com/ios-filled/50/ffffff/linkedin.png"},
    "instagram": {"bg": "#E1306C", "icon": "https://img.icons8.com/ios-filled/50/ffffff/instagram-new.png"},
}


def _social_row(pairs: list[tuple[str, str]], size: int = 32) -> str:
    cells = []
    for label, url in pairs:
        if not url:
            continue
        meta = _SOCIAL.get(label)
        if not meta:
            continue
        cells.append(
            f'<td style="padding-right:6px;">'
            f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer" style="display:inline-block;text-decoration:none;">'
            f'<table cellpadding="0" cellspacing="0" border="0"><tr>'
            f'<td width="{size}" height="{size}" style="background:{meta["bg"]};border-radius:{size//2}px;text-align:center;vertical-align:middle;">'
            f'<img src="{meta["icon"]}" width="18" height="18" alt="{label}" style="display:block;margin:auto;border:0;" />'
            f'</td></tr></table></a></td>'
        )
    if not cells:
        return ""
    return f'<table cellpadding="0" cellspacing="0" border="0"><tr>{"".join(cells)}</tr></table>'


def _logo_width_px(size) -> int:
    s = str(size or "large")
    if s.isdigit():
        return min(500, max(60, int(s)))
    return LOGO_SIZES.get(s, LOGO_SIZES["large"])


def _logo_html(sig: dict, base_url: str | None = None) -> str:
    if not sig.get("logo_url"):
        return ""
    w = _logo_width_px(sig.get("logo_size", "large"))
    return (
        f'<img src="{escape(_absolute_url(sig["logo_url"], base_url))}" alt="logo" '
        f'style="width:{w}px;max-width:{w}px;height:auto;display:block;" />'
    )


def build_signature_html(sig: dict, user: dict, base_url: str | None = None) -> str:
    """sig = entity signature config (company parts). user = the person's own
    name/email/phone/title (fetched from the directory). Always rebuilt so each
    user's identity is correct — never a stored per-user copy."""
    # All signature TEXT (name, email/website/WhatsApp/Teams links, accent bars)
    # is black per request; social icon buttons keep their own brand colours.
    accent = "#000000"
    email = user.get("email") or ""
    email_link = (
        f'<a href="mailto:{escape(email)}" style="color:{accent};text-decoration:none;">{escape(email)}</a>'
        if email else ""
    )
    website = sig.get("website") or ""
    website_link = (
        f'<a href="{escape(website)}" style="color:{accent};text-decoration:none;">{escape(website)}</a>'
        if website else ""
    )
    # Per-person WhatsApp (click-to-chat) and Teams (deep link if an email/id was
    # given, else use a full URL as-is). Rendered only when the employee has them,
    # folded into the phone block so every layout shows them with no layout edits.
    contact_lines = []
    if user.get("phone"):
        contact_lines.append(escape(str(user["phone"])))
    wa = (user.get("whatsapp") or "").strip()
    if wa:
        digits = "".join(ch for ch in wa if ch.isdigit())
        contact_lines.append(
            f'<a href="https://wa.me/{digits}" style="color:{accent};text-decoration:none;">'
            f'WhatsApp: {escape(wa)}</a>')
    tm = (user.get("teams") or "").strip()
    if tm:
        href = tm if tm.startswith("http") else f'https://teams.microsoft.com/l/chat/0/0?users={escape(tm)}'
        contact_lines.append(
            f'<a href="{escape(href)}" style="color:{accent};text-decoration:none;">Teams</a>')
    phone_block = "<br>".join(contact_lines)
    social_pairs = [
        ("facebook", sig.get("facebook") or ""), ("twitter", sig.get("twitter") or ""),
        ("youtube", sig.get("youtube") or ""), ("linkedin", sig.get("linkedin") or ""),
        ("instagram", sig.get("instagram") or ""),
    ]
    vals = SigVals(
        name=escape(user.get("name") or ""),
        title=escape(user.get("title") or "Sales Representative"),
        company=escape(sig.get("company_name") or ""),
        phone=phone_block,
        email_link=email_link,
        address=escape(sig["address"]) if sig.get("address") else "",
        website_link=website_link,
        logo_html=_logo_html(sig, base_url),
        social_html=_social_row(social_pairs),
        accent=accent,
        logo_pos=sig.get("logo_pos", "right") or "right",
        social_pos=sig.get("social_pos", "below_logo") or "below_logo",
    )
    body = render_layout(sig.get("layout", "classic") or "classic", vals)
    return f'<div style="font-family:Arial,sans-serif;margin-top:24px;">{body}</div>'
