"""The core operation: apply an entity's signature to every user in its Google
directory, personalized per user. This is what 'Save & Apply' and the scheduled
re-sync both call."""
from .. import db
from ..google_provider import get_provider
from .email_signature import build_signature_html


def _sig_config(sig_row: dict) -> dict:
    """Map the sig_settings DB row to the dict build_signature_html expects."""
    return {
        "layout": sig_row["layout"], "logo_size": sig_row["logo_size"],
        "logo_pos": sig_row["logo_pos"], "social_pos": sig_row["social_pos"],
        "company_name": sig_row["company_name"], "address": sig_row["address"],
        "website": sig_row["website"], "logo_url": sig_row["logo_url"],
        "facebook": sig_row["facebook"], "twitter": sig_row["twitter"],
        "youtube": sig_row["youtube"], "linkedin": sig_row["linkedin"],
        "instagram": sig_row["instagram"],
    }


def _wrap_with_promo(tenant_id: str, sig_html: str, base_url: str | None = None) -> str:
    promo = db.q_one(
        "SELECT * FROM promo_templates WHERE tenant_id=? AND active=1 "
        "ORDER BY created_at DESC LIMIT 1", (tenant_id,))
    if not promo:
        return sig_html
    html = promo["html"]
    # Uploaded banners are stored as site-relative /uploads/... — mail clients
    # can't resolve those, so make them absolute against the request origin.
    if base_url:
        html = html.replace('src="/uploads/', f'src="{base_url.rstrip("/")}/uploads/')
    if promo["position"] == "above":
        return html + sig_html
    return sig_html + html


def apply_signatures(tenant_id: str, base_url: str | None = None) -> dict:
    """Fetch the entity's users from Google, render each one's personalized
    signature, push it, and log the outcome. Returns a per-user result summary."""
    tenant = db.q_one("SELECT * FROM tenants WHERE id=?", (tenant_id,))
    if not tenant:
        return {"error": "tenant not found"}
    sig_row = db.ensure_sig_row(tenant_id)
    if not sig_row["enabled"]:
        return {"applied": 0, "skipped": "signature disabled", "results": []}

    provider = get_provider()
    domain = tenant["domain"] or ""
    users = provider.list_users(domain)
    cfg = _sig_config(sig_row)
    results = []
    # clear old log for this tenant so the status view reflects the latest run
    db.execute("DELETE FROM sync_log WHERE tenant_id=?", (tenant_id,))
    for u in users:
        try:
            html = build_signature_html(cfg, u, base_url)
            html = _wrap_with_promo(tenant_id, html, base_url)
            provider.set_signature(domain, u["email"], html)
            status, detail = "ok", None
        except Exception as e:  # one bad user never aborts the whole run
            status, detail = "error", str(e)
        db.execute(
            "INSERT INTO sync_log (id, tenant_id, user_email, status, detail, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (db.new_id(), tenant_id, u["email"], status, detail, db.now_ms()))
        results.append({"email": u["email"], "name": u["name"], "status": status, "detail": detail})
    return {"applied": sum(1 for r in results if r["status"] == "ok"),
            "total": len(results), "results": results}
