"""All HTTP endpoints, grouped in one router (small surface). Tenancy rule:
every admin/agent action is scoped to the caller's tenant_id; the owner is
cross-tenant."""
import json
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from .. import db
from ..auth import current_user, require_role, hash_password, verify_password, make_token
from ..google_provider import get_provider
from ..lib import sync
from ..lib.email_signature import build_signature_html

router = APIRouter(prefix="/api")

from ..db import DATA_DIR
UPLOAD_DIR = DATA_DIR / "uploads"
ALLOWED_IMG = {"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp"}
MAX_IMG = 5 * 1024 * 1024


def _shrink_for_email(data: bytes, ext: str) -> tuple[bytes, str]:
    """Gmail proxies images and often refuses to render large ones (a 1.7 MB
    banner fails while a small logo loads). Downscale to <=1000px wide and
    recompress so uploaded banners always render. Best-effort: if Pillow isn't
    installed, return the original bytes unchanged."""
    try:
        import io
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        if im.width > 1000:
            im = im.resize((1000, round(im.height * 1000 / im.width)))
        # A heavy PNG (photo banner) stays huge as PNG; if it's big and has no
        # transparency, re-encode as JPEG — far smaller, and Gmail loads it.
        heavy = len(data) > 400 * 1024
        has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
        if heavy and not has_alpha and ext != "gif":
            im = im.convert("RGB")
            out = io.BytesIO(); im.save(out, format="JPEG", quality=82, optimize=True)
            shrunk = out.getvalue()
            return (shrunk, "jpg") if len(shrunk) < len(data) else (data, ext)
        out = io.BytesIO()
        fmt = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP", "gif": "GIF"}.get(ext, "PNG")
        kw = {"optimize": True}
        if fmt == "JPEG":
            im = im.convert("RGB"); kw["quality"] = 82
        im.save(out, format=fmt, **kw)
        shrunk = out.getvalue()
        return (shrunk, ext) if len(shrunk) < len(data) else (data, ext)
    except Exception:
        return data, ext


async def _save_image(file: UploadFile, subdir: str) -> str:
    mime = file.content_type or ""
    if mime not in ALLOWED_IMG:
        raise HTTPException(422, "Only PNG, JPG, GIF or WEBP images are allowed")
    data = await file.read(MAX_IMG + 1)
    if len(data) > MAX_IMG:
        raise HTTPException(413, "Image must be under 5 MB")
    ext = {"image/png": "png", "image/gif": "gif", "image/webp": "webp"}.get(mime, "jpg")
    data, ext = _shrink_for_email(data, ext)
    d = UPLOAD_DIR / subdir
    d.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.{ext}"
    (d / name).write_bytes(data)
    return f"/uploads/{subdir}/{name}"


def _public_base(request: Request) -> str:
    """Absolute site origin for image URLs embedded in email.

    Behind a reverse proxy (Coolify/Traefik) request.base_url is often http://
    internal-host; email clients then block the mixed/insecure image and show a
    broken icon. Resolve robustly:
      1) PUBLIC_BASE_URL env var (set this to https://signature.crownitsolution.com)
      2) X-Forwarded-Proto + X-Forwarded-Host from the proxy
      3) request.base_url, upgraded to https for non-local hosts.
    """
    env = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if env:
        return env
    host = request.headers.get("x-forwarded-host") or request.url.hostname or ""
    proto = request.headers.get("x-forwarded-proto")
    if not proto:
        proto = "http" if host in ("localhost", "127.0.0.1") or host.startswith("localhost:") else "https"
    port = request.url.port
    if port and host and ":" not in host and port not in (80, 443):
        host = f"{host}:{port}"
    return f"{proto}://{host}"


# ---------- auth ----------
class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/auth/login")
def login(body: LoginIn):
    user = db.q_one("SELECT * FROM users WHERE email=?", (body.email.lower(),))
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    return {"token": make_token(user["id"]),
            "user": {"id": user["id"], "email": user["email"], "name": user["name"],
                     "role": user["role"], "tenant_id": user["tenant_id"]}}


@router.get("/auth/me")
def me(user: dict = Depends(current_user)):
    return {"id": user["id"], "email": user["email"], "name": user["name"],
            "role": user["role"], "tenant_id": user["tenant_id"]}


# ---------- tenants (owner) ----------
class TenantIn(BaseModel):
    name: str
    domain: str
    admin_email: str
    admin_name: str
    admin_password: str


@router.get("/tenants")
def list_tenants(user: dict = Depends(require_role("owner"))):
    return db.q_all("SELECT * FROM tenants ORDER BY created_at DESC")


@router.post("/tenants", status_code=201)
def create_tenant(body: TenantIn, user: dict = Depends(require_role("owner"))):
    tid = db.new_id()
    db.execute("INSERT INTO tenants (id, name, domain, google_connected, created_at) VALUES (?,?,?,?,?)",
               (tid, body.name, body.domain.lower(), 0, db.now_ms()))
    db.ensure_sig_row(tid)
    db.execute("INSERT INTO users (id, tenant_id, email, name, title, phone, password_hash, role, created_at) "
               "VALUES (?,?,?,?,?,?,?,?,?)",
               (db.new_id(), tid, body.admin_email.lower(), body.admin_name, "Administrator", None,
                hash_password(body.admin_password), "admin", db.now_ms()))
    return {"id": tid}


class TenantPatch(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None


@router.patch("/tenants/{tid}")
def edit_tenant(tid: str, body: TenantPatch, user: dict = Depends(require_role("owner"))):
    t = db.q_one("SELECT * FROM tenants WHERE id=?", (tid,))
    if not t:
        raise HTTPException(404, "Tenant not found")
    if body.name is not None:
        db.execute("UPDATE tenants SET name=? WHERE id=?", (body.name, tid))
    if body.domain is not None:
        db.execute("UPDATE tenants SET domain=? WHERE id=?", (body.domain.lower(), tid))
    return db.q_one("SELECT * FROM tenants WHERE id=?", (tid,))


@router.delete("/tenants/{tid}", status_code=204)
def remove_tenant(tid: str, user: dict = Depends(require_role("owner"))):
    """Removes the entity and everything scoped to it (ON DELETE CASCADE handles
    users, employees, sig_settings, promos, sync_log)."""
    t = db.q_one("SELECT * FROM tenants WHERE id=?", (tid,))
    if not t:
        raise HTTPException(404, "Tenant not found")
    db.execute("DELETE FROM tenants WHERE id=?", (tid,))


# ---------- signature settings (admin) ----------
def _tenant_of(user: dict) -> str:
    if not user["tenant_id"]:
        raise HTTPException(400, "No tenant for this user")
    return user["tenant_id"]


@router.get("/signature")
def get_signature(user: dict = Depends(require_role("admin"))):
    return db.ensure_sig_row(_tenant_of(user))


class SigUpdate(BaseModel):
    enabled: Optional[bool] = None
    layout: Optional[str] = None
    logo_size: Optional[str] = None
    logo_pos: Optional[str] = None
    social_pos: Optional[str] = None
    company_name: Optional[str] = None
    tagline: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    youtube: Optional[str] = None
    linkedin: Optional[str] = None
    instagram: Optional[str] = None


@router.patch("/signature")
def update_signature(body: SigUpdate, user: dict = Depends(require_role("admin"))):
    tid = _tenant_of(user)
    db.ensure_sig_row(tid)
    data = body.model_dump(exclude_unset=True)
    if data:
        sets = ", ".join(f"{k}=?" for k in data)
        vals = [int(v) if isinstance(v, bool) else v for v in data.values()]
        db.execute(f"UPDATE sig_settings SET {sets} WHERE tenant_id=?", (*vals, tid))
    return db.ensure_sig_row(tid)


@router.get("/signature/preview")
def preview(request: Request, user: dict = Depends(require_role("admin"))):
    """Live preview using the admin's own identity as the sample person."""
    tid = _tenant_of(user)
    base_url = _public_base(request)
    sig = sync._sig_config(db.ensure_sig_row(tid))
    sample = {"name": user["name"], "email": user["email"],
              "title": user["title"] or "Sales Representative", "phone": user["phone"]}
    html = build_signature_html(sig, sample, base_url)
    return {"html": sync._wrap_with_promo(tid, html, base_url)}


@router.get("/signature/export")
def export_signature(request: Request, employee_id: Optional[str] = None,
                     email: Optional[str] = None,
                     user: dict = Depends(require_role("admin"))):
    """Export the finished signature so it can be pasted straight into Gmail's
    'Settings -> Signature' box (like any signature-maker site). Returns the same
    email-safe HTML the recipient sees, plus a standalone HTML document to
    download and share. Identity precedence: ?employee_id= (that agent's stored
    record) -> ?email= (a recipient on this tenant's domain; name/title pulled
    from the directory if listed, else derived from the address) -> the admin.
    Each agent thus gets a ready-to-paste copy with no editing."""
    tid = _tenant_of(user)
    base_url = _public_base(request)
    sig = sync._sig_config(db.ensure_sig_row(tid))
    if employee_id:
        emp = db.q_one("SELECT * FROM employees WHERE id=? AND tenant_id=?", (employee_id, tid))
        if not emp:
            raise HTTPException(404, "Employee not found")
        person = {"name": emp["name"], "email": emp["email"],
                  "title": emp["title"] or "Sales Representative", "phone": emp["phone"]}
    elif email:
        addr = email.strip().lower()
        t = db.q_one("SELECT * FROM tenants WHERE id=?", (tid,))
        if t["domain"] and not addr.endswith("@" + t["domain"]):
            raise HTTPException(422, "Email is not on this entity's domain")
        emp = db.q_one("SELECT * FROM employees WHERE email=? AND tenant_id=?", (addr, tid))
        if emp:
            person = {"name": emp["name"], "email": emp["email"],
                      "title": emp["title"] or "Sales Representative", "phone": emp["phone"]}
        else:
            local = addr.split("@", 1)[0].replace(".", " ").replace("_", " ")
            person = {"name": local.title(), "email": addr,
                      "title": "Sales Representative", "phone": ""}
    else:
        person = {"name": user["name"], "email": user["email"],
                  "title": user["title"] or "Sales Representative", "phone": user["phone"]}
    html = sync._wrap_with_promo(tid, build_signature_html(sig, person, base_url), base_url)
    document = ('<!doctype html><html><head><meta charset="utf-8">'
                '<title>Email signature</title></head><body>' + html + '</body></html>')
    return {"html": html, "document": document, "for": person["email"]}


@router.post("/signature/test")
def send_test(request: Request, user: dict = Depends(require_role("admin"))):
    """Send-test: renders the signature exactly as a recipient would see it, with
    the admin as the sample sender. ponytail: returns the rendered HTML instead of
    posting real mail (no SMTP/Workspace wired). Swap in a real send here — the
    HTML is already final and email-safe."""
    tid = _tenant_of(user)
    base_url = _public_base(request)
    sig = sync._sig_config(db.ensure_sig_row(tid))
    sample = {"name": user["name"], "email": user["email"],
              "title": user["title"] or "Sales Representative", "phone": user["phone"]}
    html = sync._wrap_with_promo(tid, build_signature_html(sig, sample, base_url), base_url)
    return {"sent_to": user["email"], "note": "Preview render (no mail server wired yet)", "html": html}


# ---------- saved signature designs (admin) ----------
DESIGN_FIELDS = ["layout", "logo_size", "logo_pos", "social_pos",
                 "company_name", "tagline", "address", "website", "logo_url",
                 "phone", "email", "facebook", "twitter", "youtube", "linkedin", "instagram"]


class SigTemplateIn(BaseModel):
    name: str


@router.get("/sig-templates")
def list_sig_templates(user: dict = Depends(require_role("admin"))):
    return db.q_all("SELECT id, name, created_at FROM sig_templates WHERE tenant_id=? "
                    "ORDER BY created_at DESC", (_tenant_of(user),))


@router.post("/sig-templates", status_code=201)
def save_sig_template(body: SigTemplateIn, user: dict = Depends(require_role("admin"))):
    """Snapshot the entity's CURRENT signature design into a reusable template."""
    tid = _tenant_of(user)
    row = db.ensure_sig_row(tid)
    design = {k: row[k] for k in DESIGN_FIELDS}
    db.execute("INSERT INTO sig_templates (id, tenant_id, name, design_json, created_at) "
               "VALUES (?,?,?,?,?)",
               (db.new_id(), tid, body.name, json.dumps(design), db.now_ms()))
    return {"ok": True}


@router.post("/sig-templates/{sid}/apply")
def apply_sig_template(sid: str, user: dict = Depends(require_role("admin"))):
    tid = _tenant_of(user)
    row = db.q_one("SELECT * FROM sig_templates WHERE id=? AND tenant_id=?", (sid, tid))
    if not row:
        raise HTTPException(404, "Template not found")
    design = json.loads(row["design_json"])
    sets = ", ".join(f"{k}=?" for k in design)
    db.execute(f"UPDATE sig_settings SET {sets} WHERE tenant_id=?", (*design.values(), tid))
    return db.ensure_sig_row(tid)


@router.delete("/sig-templates/{sid}", status_code=204)
def delete_sig_template(sid: str, user: dict = Depends(require_role("admin"))):
    db.execute("DELETE FROM sig_templates WHERE id=? AND tenant_id=?", (sid, _tenant_of(user)))


# ---------- promo templates (admin) ----------
class PromoIn(BaseModel):
    name: str
    html: str
    position: str = "above"


@router.get("/promos")
def list_promos(user: dict = Depends(require_role("admin"))):
    return db.q_all("SELECT * FROM promo_templates WHERE tenant_id=? ORDER BY created_at DESC",
                    (_tenant_of(user),))


@router.post("/promos", status_code=201)
def create_promo(body: PromoIn, user: dict = Depends(require_role("admin"))):
    pid = db.new_id()
    db.execute("INSERT INTO promo_templates (id, tenant_id, name, html, position, active, created_at) "
               "VALUES (?,?,?,?,?,0,?)",
               (pid, _tenant_of(user), body.name, body.html, body.position, db.now_ms()))
    return {"id": pid}


@router.post("/promos/{pid}/activate")
def activate_promo(pid: str, user: dict = Depends(require_role("admin"))):
    tid = _tenant_of(user)
    p = db.q_one("SELECT * FROM promo_templates WHERE id=? AND tenant_id=?", (pid, tid))
    if not p:
        raise HTTPException(404, "Promo not found")
    db.execute("UPDATE promo_templates SET active=0 WHERE tenant_id=?", (tid,))  # single active
    db.execute("UPDATE promo_templates SET active=1 WHERE id=?", (pid,))
    return {"active": pid}


@router.post("/promos/{pid}/deactivate")
def deactivate_promo(pid: str, user: dict = Depends(require_role("admin"))):
    tid = _tenant_of(user)
    db.execute("UPDATE promo_templates SET active=0 WHERE id=? AND tenant_id=?", (pid, tid))
    return {"active": None}


@router.delete("/promos/{pid}", status_code=204)
def delete_promo(pid: str, user: dict = Depends(require_role("admin"))):
    db.execute("DELETE FROM promo_templates WHERE id=? AND tenant_id=?", (pid, _tenant_of(user)))


# ---------- apply / sync (admin) ----------
@router.get("/directory")
def directory(user: dict = Depends(require_role("admin"))):
    """Preview the users that will receive the signature (from Google)."""
    tid = _tenant_of(user)
    t = db.q_one("SELECT * FROM tenants WHERE id=?", (tid,))
    return get_provider().list_users(t["domain"] or "")


@router.post("/apply")
def apply(request: Request, user: dict = Depends(require_role("admin"))):
    """Render + store each employee's personalized signature. Delivery is via the
    Gmail browser extension (GET /api/resolve), so no Google Workspace connection
    is required. (The optional Workspace auto-push path lives behind
    GOOGLE_MODE=real / RealGoogleProvider and is not gated here.)"""
    tid = _tenant_of(user)
    base_url = _public_base(request)
    return sync.apply_signatures(tid, base_url)


@router.get("/sync-log")
def sync_log(user: dict = Depends(require_role("admin"))):
    return db.q_all("SELECT * FROM sync_log WHERE tenant_id=? ORDER BY created_at DESC",
                    (_tenant_of(user),))


@router.get("/verify/{email}")
def verify_applied(email: str, user: dict = Depends(require_role("admin"))):
    """Proof the signature landed: read it back from the (mock) Gmail store."""
    tid = _tenant_of(user)
    t = db.q_one("SELECT * FROM tenants WHERE id=?", (tid,))
    html = get_provider().get_signature(t["domain"] or "", email)
    return {"email": email, "html": html}


# ---------- employees / directory management (admin) ----------
class EmployeeIn(BaseModel):
    email: str
    name: str
    title: Optional[str] = None
    phone: Optional[str] = None


@router.get("/employees")
def list_employees(user: dict = Depends(require_role("admin"))):
    return db.q_all("SELECT * FROM employees WHERE tenant_id=? ORDER BY name",
                    (_tenant_of(user),))


@router.post("/employees", status_code=201)
def add_employee(body: EmployeeIn, user: dict = Depends(require_role("admin"))):
    tid = _tenant_of(user)
    t = db.q_one("SELECT * FROM tenants WHERE id=?", (tid,))
    email = body.email.strip().lower()
    if t["domain"] and not email.endswith("@" + t["domain"]):
        raise HTTPException(422, f"Email must be on this entity's domain (@{t['domain']})")
    try:
        db.execute("INSERT INTO employees (id, tenant_id, email, name, title, phone, created_at) "
                   "VALUES (?,?,?,?,?,?,?)",
                   (db.new_id(), tid, email, body.name, body.title, body.phone, db.now_ms()))
    except Exception:
        raise HTTPException(409, "Employee with this email already exists")
    return {"ok": True}


@router.delete("/employees/{eid}", status_code=204)
def delete_employee(eid: str, user: dict = Depends(require_role("admin"))):
    tid = _tenant_of(user)
    # Only delete if the employee belongs to THIS tenant; 404 otherwise so an
    # admin can neither remove nor probe another entity's employees.
    row = db.q_one("SELECT id FROM employees WHERE id=? AND tenant_id=?", (eid, tid))
    if not row:
        raise HTTPException(404, "Employee not found")
    db.execute("DELETE FROM employees WHERE id=? AND tenant_id=?", (eid, tid))


# ---------- image uploads (admin) ----------
@router.post("/signature/logo")
async def upload_logo(file: UploadFile = File(...), user: dict = Depends(require_role("admin"))):
    tid = _tenant_of(user)
    url = await _save_image(file, "logos")
    db.ensure_sig_row(tid)
    db.execute("UPDATE sig_settings SET logo_url=? WHERE tenant_id=?", (url, tid))
    return {"url": url}


@router.post("/promos/upload")
async def upload_promo_image(file: UploadFile = File(...), user: dict = Depends(require_role("admin"))):
    """Upload an already-generated banner image; returns ready-to-store <img> HTML."""
    _tenant_of(user)
    url = await _save_image(file, "promos")
    html = f'<div style="padding:8px 0;"><img src="{url}" alt="promotion" style="max-width:600px;width:100%;display:block;" /></div>'
    return {"url": url, "html": html}


# ---------- browser-extension client (public, no login) ----------
@router.get("/resolve")
def resolve(email: str, request: Request):
    """Called by the Gmail extension for the logged-in employee.

    DOMAIN-WIDE (Option B): the entity is picked by the email DOMAIN, and EVERY
    address on that company's domain gets the company's signature — so no one is
    missed (new hires are covered automatically). The Directory list still
    supplies each person's name/title/phone when present; addresses not on the
    list get a name derived from the local-part. Cross-company mixing is still
    impossible because the domain determines the entity.
    No auth: the extension only ever knows the current user's own address."""
    email = (email or "").strip().lower()
    domain = email.split("@")[-1] if "@" in email else ""
    if not domain:
        raise HTTPException(400, "invalid email")
    tenant = db.q_one("SELECT * FROM tenants WHERE domain=?", (domain,))
    if not tenant:
        return {"found": False, "reason": "domain not registered"}
    sig_row = db.ensure_sig_row(tenant["id"])
    if not sig_row["enabled"]:
        return {"found": False, "reason": "signature disabled"}

    # Use the directory entry when the address is listed (real name/title/phone),
    # otherwise derive a display name from the local-part so unlisted staff are
    # still covered.
    person = next((u for u in get_provider().list_users(domain) if u["email"] == email), None)
    if person is None:
        local = email.split("@")[0].replace(".", " ").replace("_", " ").title()
        person = {"email": email, "name": local, "title": None, "phone": None}

    base_url = _public_base(request)
    html = build_signature_html(sync._sig_config(sig_row), person, base_url)
    html = sync._wrap_with_promo(tenant["id"], html, base_url)
    return {"found": True, "entity": tenant["name"], "name": person["name"], "html": html}
