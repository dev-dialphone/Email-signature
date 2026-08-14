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
# Option A (list-only): an address NOT on the entity's list gets nothing, even on a registered domain.
r2 = c.get(f"/api/resolve?email=random@{d1}").json()
check("resolve non-listed email -> not found (list-only)", r2["found"] is False and "list" in r2.get("reason", ""))
check("resolve empty email -> 400", c.get("/api/resolve?email=").status_code == 400)
# isolation: acme resolve must not leak beta
check("resolve no cross-tenant leak", "BETA" not in r["html"].upper())

print("== DELETE / CASCADE ==")
check("delete own template ok", c.delete(f"/api/sig-templates/{sid}", headers=H(a1)).status_code == 204)
r = c.delete(f"/api/tenants/{t1['id']}", headers=H(owner))
check("owner delete tenant -> 204", r.status_code == 204)
check("resolve after tenant delete -> not found", c.get(f"/api/resolve?email=asha@{d1}").json()["found"] is False)

print(f"\n==== RESULT: {_passed} passed, {_failed} failed ====")
sys.exit(1 if _failed else 0)
