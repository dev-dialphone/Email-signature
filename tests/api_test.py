"""Full backend/API test suite. Spins the app in-process (TestClient), exercises
every endpoint + edge cases + RBAC + multi-tenant isolation. Runs against SQLite
by default; set DATABASE_URL to also cover Postgres. No external test framework —
plain asserts + a tiny runner, so it works with just the app's deps."""
import io
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

# Fresh isolated data dir per run (SQLite mode).
os.environ.setdefault("DATA_DIR", f"/tmp/apitest_{uuid.uuid4().hex}")

from fastapi.testclient import TestClient  # noqa: E402
from backend.main import app, seed  # noqa: E402

seed()
c = TestClient(app)

_passed = 0
_failed = 0


def check(name, cond):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        _failed += 1
        print(f"  FAIL  {name}")


def png_bytes(w=1200, h=300):
    try:
        from PIL import Image
        b = io.BytesIO(); Image.new("RGB", (w, h), (30, 120, 200)).save(b, "PNG")
        return b.getvalue()
    except Exception:
        # minimal 1x1 png
        import base64
        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")


def login(email, pw):
    r = c.post("/api/auth/login", json={"email": email, "password": pw})
    return r.json().get("token") if r.status_code == 200 else None


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


print("== AUTH ==")
check("wrong password -> 401", c.post("/api/auth/login", json={"email": "owner@platform.com", "password": "x"}).status_code == 401)
check("unknown user -> 401", c.post("/api/auth/login", json={"email": "nobody@x.com", "password": "x"}).status_code == 401)
owner = login("owner@platform.com", "owner123")
check("owner login ok", bool(owner))
check("me returns owner role", c.get("/api/auth/me", headers=H(owner)).json().get("role") == "owner")
check("me without token -> 401", c.get("/api/auth/me").status_code == 401)
check("me with forged token -> 401", c.get("/api/auth/me", headers=H("a.b.c")).status_code == 401)

print("== TENANTS (owner) ==")
d1 = f"acme{uuid.uuid4().hex[:6]}.com"
d2 = f"beta{uuid.uuid4().hex[:6]}.com"
r = c.post("/api/tenants", headers=H(owner), json={"name": "Acme", "domain": d1, "admin_name": "AA", "admin_email": f"admin@{d1}", "admin_password": "pw1"})
check("create tenant -> 201", r.status_code == 201)
c.post("/api/tenants", headers=H(owner), json={"name": "Beta", "domain": d2, "admin_name": "BB", "admin_email": f"admin@{d2}", "admin_password": "pw2"})
tenants = c.get("/api/tenants", headers=H(owner)).json()
t1 = next(t for t in tenants if t["domain"] == d1)
t2 = next(t for t in tenants if t["domain"] == d2)
check("edit tenant name", c.patch(f"/api/tenants/{t1['id']}", headers=H(owner), json={"name": "Acme2"}).json()["name"] == "Acme2")
check("edit missing tenant -> 404", c.patch(f"/api/tenants/{uuid.uuid4()}", headers=H(owner), json={"name": "x"}).status_code == 404)

a1 = login(f"admin@{d1}", "pw1")
a2 = login(f"admin@{d2}", "pw2")
check("tenant admin login ok", bool(a1) and bool(a2))

print("== RBAC ==")
check("admin cannot list tenants -> 403", c.get("/api/tenants", headers=H(a1)).status_code == 403)
check("admin cannot delete tenant -> 403", c.delete(f"/api/tenants/{t2['id']}", headers=H(a1)).status_code == 403)
check("owner has no tenant for signature -> 400", c.get("/api/signature", headers=H(owner)).status_code in (400, 403))

print("== SIGNATURE ==")
check("get signature ok", c.get("/api/signature", headers=H(a1)).status_code == 200)
# minimal & compact are the deliberately terse layouts: they show name/title/contact
# but intentionally OMIT the company name. Assert company only where the design includes it.
NO_COMPANY = {"minimal", "compact"}
for lay in ["classic", "modern", "minimal", "bold", "compact", "stacked", "stacked_social_bottom", "arranged"]:
    r = c.patch("/api/signature", headers=H(a1), json={"enabled": True, "layout": lay, "company_name": "ACME CORP", "website": "https://acme.com"})
    check(f"patch layout {lay}", r.status_code == 200 and r.json()["layout"] == lay)
    pv = c.get("/api/signature/preview", headers=H(a1)).json()
    ok = "<table" in pv["html"]  # table-based HTML rendered
    if lay not in NO_COMPANY:
        ok = ok and "ACME CORP" in pv["html"]
    check(f"preview {lay} renders", ok)
check("send test ok", c.post("/api/signature/test", headers=H(a1)).status_code == 200)
ex = c.get("/api/signature/export", headers=H(a1))
check("export ok", ex.status_code == 200 and "<table" in ex.json()["html"])
check("export document is standalone", "<!doctype html" in ex.json()["document"].lower())
check("export requires admin -> 401", c.get("/api/signature/export").status_code == 401)

print("== EMPLOYEES ==")
r = c.post("/api/employees", headers=H(a1), json={"name": "Asha", "email": f"asha@{d1}", "title": "Sales"})
check("add employee ok", r.status_code == 201)
check("dup employee -> 409", c.post("/api/employees", headers=H(a1), json={"name": "Asha", "email": f"asha@{d1}"}).status_code == 409)
check("wrong-domain employee -> 422", c.post("/api/employees", headers=H(a1), json={"name": "X", "email": f"x@{d2}"}).status_code == 422)
emps = c.get("/api/employees", headers=H(a1)).json()
check("list employees own only", [e["email"] for e in emps] == [f"asha@{d1}"])
eid = emps[0]["id"]
check("cross-tenant delete employee -> 404", c.delete(f"/api/employees/{eid}", headers=H(a2)).status_code == 404)
check("employee still there after cross attempt", len(c.get("/api/employees", headers=H(a1)).json()) == 1)
# Per-agent export: renders THAT agent's real identity (ready to paste), scoped to tenant.
ee = c.get(f"/api/signature/export?employee_id={eid}", headers=H(a1)).json()
check("per-agent export uses agent identity", "Asha" in ee["html"] and f"asha@{d1}" in ee["html"] and ee["for"] == f"asha@{d1}")
check("cross-tenant employee export -> 404", c.get(f"/api/signature/export?employee_id={eid}", headers=H(a2)).status_code == 404)
check("export unknown employee -> 404", c.get(f"/api/signature/export?employee_id=nope", headers=H(a1)).status_code == 404)
# Export by email (Apply & Status page): listed -> real record; unlisted -> derived name.
el = c.get(f"/api/signature/export?email=asha@{d1}", headers=H(a1)).json()
check("export by email (listed) uses record", "Asha" in el["html"] and el["for"] == f"asha@{d1}")
eu = c.get(f"/api/signature/export?email=ravi.kumar@{d1}", headers=H(a1)).json()
check("export by email (unlisted) derives name", "Ravi Kumar" in eu["html"] and eu["for"] == f"ravi.kumar@{d1}")
check("export off-domain email -> 422", c.get(f"/api/signature/export?email=x@{d2}", headers=H(a1)).status_code == 422)

print("== SIG TEMPLATES ==")
check("save template -> 201", c.post("/api/sig-templates", headers=H(a1), json={"name": "T1"}).status_code == 201)
sid = c.get("/api/sig-templates", headers=H(a1)).json()[0]["id"]
check("apply own template ok", c.post(f"/api/sig-templates/{sid}/apply", headers=H(a1)).status_code == 200)
check("cross-tenant apply template -> 404", c.post(f"/api/sig-templates/{sid}/apply", headers=H(a2)).status_code == 404)
check("other admin sees no templates", c.get("/api/sig-templates", headers=H(a2)).json() == [])

print("== UPLOADS ==")
r = c.post("/api/signature/logo", headers=H(a1), files={"file": ("logo.png", png_bytes(240, 80), "image/png")})
check("logo upload ok", r.status_code == 200 and r.json()["url"].startswith("/uploads/"))
check("logo served", c.get(r.json()["url"]).status_code == 200)
r = c.post("/api/promos/upload", headers=H(a1), files={"file": ("banner.png", png_bytes(1600, 400), "image/png")})
check("promo upload ok", r.status_code == 200)
check("bad mime rejected -> 422", c.post("/api/promos/upload", headers=H(a1), files={"file": ("x.txt", b"hello", "text/plain")}).status_code == 422)

print("== PROMOS ==")
purl = "https://raw.githubusercontent.com/x/y/main/banner.jpeg"
phtml = f'<div><img src="{purl}" width="600"/></div>'
check("create promo -> 201", c.post("/api/promos", headers=H(a1), json={"name": "Sale", "html": phtml, "position": "above"}).status_code == 201)
pid = c.get("/api/promos", headers=H(a1)).json()[0]["id"]
check("activate promo ok", c.post(f"/api/promos/{pid}/activate", headers=H(a1)).status_code == 200)
check("cross-tenant activate -> 404", c.post(f"/api/promos/{pid}/activate", headers=H(a2)).status_code == 404)
check("deactivate ok", c.post(f"/api/promos/{pid}/deactivate", headers=H(a1)).status_code == 200)

print("== APPLY ==")
c.post(f"/api/promos/{pid}/activate", headers=H(a1))
r = c.post("/api/apply", headers=H(a1)).json()
check("apply applies to employees", r.get("applied") == 1 and r.get("total") == 1)
log = c.get("/api/sync-log", headers=H(a1)).json()
check("sync log recorded", len(log) == 1 and log[0]["status"] == "ok")

print("== RESOLVE (public extension) ==")
r = c.get(f"/api/resolve?email=asha@{d1}").json()
check("resolve found + personalized", r["found"] and "Asha" in r["html"] and f"asha@{d1}" in r["html"])
check("resolve embeds active promo", "banner.jpeg" in r["html"])
check("resolve unknown domain -> not found", c.get("/api/resolve?email=x@nope-nope.com").json()["found"] is False)
# Option B (domain-wide): any address on a registered domain is covered; unlisted
# staff get a name derived from the local-part.
r2 = c.get(f"/api/resolve?email=random@{d1}").json()
check("resolve unlisted email covered (domain-wide)", r2["found"] and r2["name"].lower() == "random")
check("resolve empty email -> 400", c.get("/api/resolve?email=").status_code == 400)
# isolation: acme resolve must not leak beta
check("resolve no cross-tenant leak", "BETA" not in r["html"].upper())

# Per-domain routing (the extension resolves by the sender's exact domain).
# Give company B a distinctive signature so we can detect mis-routing.
c.patch("/api/signature", headers=H(a2), json={"enabled": True, "company_name": "BETA UNIQUE CO"})
ra = c.get(f"/api/resolve?email=someone@{d1}").json()
rb = c.get(f"/api/resolve?email=someone@{d2}").json()
check("domain d1 -> entity Acme only", ra["entity"] == "Acme2" and "BETA UNIQUE CO" not in ra["html"])
check("domain d2 -> entity Beta only", rb["entity"] == "Beta" and "BETA UNIQUE CO" in rb["html"] and "ACME CORP" not in rb["html"])
check("plus-addressing routes by domain", c.get(f"/api/resolve?email=sales.team+promo@{d1}").json()["entity"] == "Acme2")
check("case-insensitive email routes", c.get(f"/api/resolve?email=UPPER@{d1.upper()}").json()["entity"] == "Acme2")
check("subdomain of registered domain does NOT match", c.get(f"/api/resolve?email=x@mail.{d1}").json()["found"] is False)
check("lookalike domain does NOT match", c.get(f"/api/resolve?email=x@{d1}.evil.com").json()["found"] is False)

print("== DELETE / CASCADE ==")
check("delete own template ok", c.delete(f"/api/sig-templates/{sid}", headers=H(a1)).status_code == 204)
r = c.delete(f"/api/tenants/{t1['id']}", headers=H(owner))
check("owner delete tenant -> 204", r.status_code == 204)
check("resolve after tenant delete -> not found", c.get(f"/api/resolve?email=asha@{d1}").json()["found"] is False)

print(f"\n==== RESULT: {_passed} passed, {_failed} failed ====")
sys.exit(1 if _failed else 0)
