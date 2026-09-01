"""Render an entity's signature template with a single user's own values.
Ported from the extracted module; the `settings.PUBLIC_BASE_URL` dependency is
replaced by a plain base_url argument (standalone app has no global settings)."""
from html import escape
from .sig_layouts import SigVals, LOGO_SIZES, render_layout
from .sig_theme import theme_for


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


def _social_row(pairs: list[tuple[str, str]], size: int = 32, icon_style: str = "circle") -> str:
    # icon_style controls the button shape so entities look visually distinct:
    #   circle -> filled round button (original)
    #   square -> filled rounded-rectangle button
    #   plain  -> brand-colour glyph on transparent bg (no filled button)
    cells = []
    for label, url in pairs:
        if not url:
            continue
        meta = _SOCIAL.get(label)
        if not meta:
            continue
        if icon_style == "plain":
            # coloured icon (brand tint) on no background
            glyph = meta["icon"].replace("/ffffff/", f'/{meta["bg"].lstrip("#")}/')
            inner = (f'<td width="{size}" height="{size}" style="text-align:center;vertical-align:middle;">'
                     f'<img src="{glyph}" width="22" height="22" alt="{label}" style="display:block;margin:auto;border:0;" /></td>')
        else:
            radius = size // 2 if icon_style == "circle" else 6
            inner = (f'<td width="{size}" height="{size}" style="background:{meta["bg"]};'
                     f'border-radius:{radius}px;text-align:center;vertical-align:middle;">'
                     f'<img src="{meta["icon"]}" width="18" height="18" alt="{label}" style="display:block;margin:auto;border:0;" /></td>')
        cells.append(
            f'<td style="padding-right:6px;">'
            f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer" style="display:inline-block;text-decoration:none;">'
            f'<table cellpadding="0" cellspacing="0" border="0"><tr>{inner}</tr></table></a></td>'
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
    # Per-entity theme (hardcoded, keyed by the sender's email domain) so
    # different entities don't look alike. Unknown domains -> DialPhone default
    # (black text, circle icons). Social icon buttons keep their brand colours.
    email = user.get("email") or ""
    domain = email.split("@", 1)[1].lower() if "@" in email else (sig.get("domain") or "")
    theme = theme_for(domain)
    accent = theme["accent"]
    icon_style = theme.get("icon_style", "circle")
    # Show the email line only when the person has no Teams contact; when Teams is
    # set, it replaces the email line in the signature (per request). Values are
    # always rendered exactly as entered — no .com/.ai rewriting.
    has_teams = bool((user.get("teams") or "").strip())
    email_link = (
        f'<a href="mailto:{escape(email)}" style="color:{accent};text-decoration:none;">{escape(email)}</a>'
        if email and not has_teams else ""
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
            f'<a href="{escape(href)}" style="color:{accent};text-decoration:none;">Teams: {escape(tm)}</a>')
    phone_block = "<br>".join(contact_lines)
    social_pairs = [
        ("facebook", sig.get("facebook") or ""), ("twitter", sig.get("twitter") or ""),
        ("youtube", sig.get("youtube") or ""), ("linkedin", sig.get("linkedin") or ""),
        ("instagram", sig.get("instagram") or ""),
    ]
    # Title: bold + dark like name/company (was faint grey). Wrapping the value
    # itself carries the styling into every layout with no per-layout edits.
    _title = escape(user.get("title") or "Sales Representative")
    title_html = f'<strong style="color:#333333;">{_title}</strong>' if _title else ""
    vals = SigVals(
        name=escape(user.get("name") or ""),
        title=title_html,
        company=escape(sig.get("company_name") or ""),
        phone=phone_block,
        email_link=email_link,
        address=escape(sig["address"]) if sig.get("address") else "",
        website_link=website_link,
        logo_html=_logo_html(sig, base_url),
        social_html=_social_row(social_pairs, icon_style=icon_style),
        accent=accent,
        text=theme.get("text", "#333333"),
        logo_pos=sig.get("logo_pos", "right") or "right",
        social_pos=sig.get("social_pos", "below_logo") or "below_logo",
    )
    # The admin's chosen layout ALWAYS wins (so the Design picker works); the
    # theme only supplies a starting default the first time, when no layout is
    # saved yet. Entities still look distinct via accent colour + icon style.
    layout = sig.get("layout") or theme.get("layout") or "classic"
    body = render_layout(layout, vals)
    return f'<div style="font-family:Arial,sans-serif;margin-top:24px;">{body}</div>'
