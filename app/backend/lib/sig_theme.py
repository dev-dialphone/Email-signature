"""Per-entity hardcoded visual themes so signatures from different entities do
NOT look alike or related. Resolved by the sender's email domain. Every listed
entity gets its OWN accent colour, social-icon style AND default layout — no two
entities share any of the three. Unknown domains fall back to DEFAULT.

Adding a new entity = add one line to THEMES; give it an accent/icon_style/layout
not already used by another entity.

icon_style: 'circle' (filled round brand button) | 'square' (brand rounded rect) |
'plain' (brand-colour glyph, no button) | 'accent_round' (solid accent round) |
'accent_square' (solid accent rounded rect) | 'outline' (white, accent border) |
'mono' (charcoal round button)."""

# Fallback for any unlisted domain (the original DialPhone look).
DEFAULT = {
    "accent": "#000000",       # link/name colour
    "text": "#333333",         # body text colour
    "icon_style": "circle",
    "layout": None,            # None = keep whatever layout the admin picked
}

# Distinct presets, keyed by exact registered domain (lowercase).
# INVARIANT: unique accent + unique icon_style + unique layout per entity.
THEMES = {
    # DialPhone family — the original look (circle icons, admin-chosen layout).
    "dialphone.com": DEFAULT,
    "dialphone.ai":  DEFAULT,

    "easedial.com":      {"accent": "#0F7B7B", "text": "#222222", "icon_style": "square",        "layout": "banner_top"},
    "vestacall.com":     {"accent": "#6B21A8", "text": "#222222", "icon_style": "plain",         "layout": "elegant"},
    # Salamtalk brand blue (the wifi mark in their logo).
    "salamtalk.com":     {"accent": "#1CA9E3", "text": "#222222", "icon_style": "outline",       "layout": "card"},
    "mycallconnect.com": {"accent": "#1D4ED8", "text": "#222222", "icon_style": "accent_round",  "layout": "sidebar"},
}


def theme_for(domain: str | None) -> dict:
    """Return the visual theme for a domain, falling back to DEFAULT."""
    if not domain:
        return DEFAULT
    return THEMES.get(domain.strip().lower(), DEFAULT)
