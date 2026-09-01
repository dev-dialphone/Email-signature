"""Per-entity hardcoded visual themes so signatures from different entities do
NOT look like they belong to the same company. Resolved by the sender's email
domain. DialPhone keeps the current look (the DEFAULT); every other listed
entity gets a distinct accent colour, social-icon shape and default layout.

Adding a new entity = add one line to THEMES keyed by its domain. Unknown
domains fall back to DEFAULT (current DialPhone look), so nothing breaks.

icon_style: 'circle' (filled round button, current) | 'square' (rounded rect) |
'plain' (brand-colour glyph, no filled button)."""

# The original DialPhone look — also the fallback for any unlisted domain.
DEFAULT = {
    "accent": "#000000",       # link/name colour
    "text": "#333333",         # body text colour
    "icon_style": "circle",
    "layout": None,            # None = keep whatever layout the admin picked
}

# Distinct presets. Keyed by exact registered domain (lowercase).
THEMES = {
    # DialPhone family — explicitly the current look.
    "dialphone.com": DEFAULT,
    "dialphone.ai":  DEFAULT,

    # Each other entity: different accent + icon shape + a different default
    # layout so the structure itself differs, not just colour.
    "easedial.com":  {"accent": "#0F7B7B", "text": "#222222", "icon_style": "square", "layout": "banner_top"},
    "vestacall.com": {"accent": "#6B21A8", "text": "#222222", "icon_style": "plain",  "layout": "elegant"},
    "salamtalk.com": {"accent": "#C2410C", "text": "#222222", "icon_style": "square", "layout": "card"},
    "mycallconnect.com": {"accent": "#1D4ED8", "text": "#222222", "icon_style": "circle", "layout": "sidebar"},
}


def theme_for(domain: str | None) -> dict:
    """Return the visual theme for a domain, falling back to DEFAULT."""
    if not domain:
        return DEFAULT
    return THEMES.get(domain.strip().lower(), DEFAULT)
