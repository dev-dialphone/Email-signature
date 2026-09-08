"""Google Workspace integration seam.

Two implementations behind one interface:
  - MockGoogleProvider  : in-memory fake directory + signature store, so the whole
                          app runs end-to-end locally with NO Google account.
  - RealGoogleProvider  : stub showing exactly where the real Directory API +
                          gmail.users.settings.sendAs.update calls go. Fill in
                          when you have a Workspace domain + delegated service
                          account. Not wired until GOOGLE_MODE=real.

The rest of the app only ever calls get_provider(); swapping is one env var.
"""
import os


class GoogleProvider:
    def list_users(self, domain: str) -> list[dict]:
        """Return [{email, name, title, phone}] for the entity's domain."""
        raise NotImplementedError

    def set_signature(self, domain: str, user_email: str, html: str) -> None:
        """Write `html` as that user's Gmail sendAs signature."""
        raise NotImplementedError

    def get_signature(self, domain: str, user_email: str) -> str | None:
        raise NotImplementedError


class MockGoogleProvider(GoogleProvider):
    """Stand-in for the real Workspace directory when GOOGLE_MODE != real. The
    directory is the admin-managed `employees` table (no fake seed data), so the
    apply/resolve flow is fully testable with real, user-entered people. Applied
    signatures are held in memory to prove the round-trip (set -> get)."""

    def __init__(self):
        self._applied: dict[tuple[str, str], str] = {}

    def list_users(self, domain: str) -> list[dict]:
        from . import db  # local import avoids a cycle at module load
        tenant = db.q_one("SELECT id FROM tenants WHERE domain=?", (domain,))
        if not tenant:
            return []
        rows = db.q_all(
            "SELECT id, email, name, title, phone, whatsapp, teams FROM employees "
            "WHERE tenant_id=? ORDER BY name",
            (tenant["id"],))
        return rows

    def set_signature(self, domain: str, user_email: str, html: str) -> None:
        self._applied[(domain, user_email)] = html

    def get_signature(self, domain: str, user_email: str) -> str | None:
        return self._applied.get((domain, user_email))


class RealGoogleProvider(GoogleProvider):
    """Real Workspace calls. Requires: a Google Cloud project, a service account
    with domain-wide delegation, and the Workspace super-admin having authorized
    scopes: admin.directory.user.readonly, gmail.settings.basic.

    Uncomment and install google-api-python-client + google-auth to activate.
    """

    def _service(self, domain: str, subject: str, api: str, version: str, scopes: list[str]):
        raise NotImplementedError(
            "RealGoogleProvider not configured. Provide a service-account JSON via "
            "GOOGLE_SA_JSON and set GOOGLE_MODE=real. See RealGoogleProvider docstring."
        )
        # from google.oauth2 import service_account
        # from googleapiclient.discovery import build
        # creds = service_account.Credentials.from_service_account_file(
        #     os.environ["GOOGLE_SA_JSON"], scopes=scopes, subject=subject)
        # return build(api, version, credentials=creds, cache_discovery=False)

    def list_users(self, domain: str) -> list[dict]:
        # svc = self._service(domain, f"admin@{domain}", "admin", "directory_v1",
        #     ["https://www.googleapis.com/auth/admin.directory.user.readonly"])
        # res = svc.users().list(domain=domain, maxResults=500).execute()
        # return [{"email": u["primaryEmail"],
        #          "name": u["name"]["fullName"],
        #          "title": u.get("organizations",[{}])[0].get("title"),
        #          "phone": (u.get("phones") or [{}])[0].get("value")}
        #         for u in res.get("users", [])]
        raise NotImplementedError

    def set_signature(self, domain: str, user_email: str, html: str) -> None:
        # svc = self._service(domain, user_email, "gmail", "v1",
        #     ["https://www.googleapis.com/auth/gmail.settings.basic"])
        # send_as = svc.users().settings().sendAs()
        # send_as.update(userId="me", sendAsEmail=user_email,
        #                body={"signature": html}).execute()
        raise NotImplementedError

    def get_signature(self, domain: str, user_email: str) -> str | None:
        raise NotImplementedError


_PROVIDER: GoogleProvider | None = None


def get_provider() -> GoogleProvider:
    global _PROVIDER
    if _PROVIDER is None:
        _PROVIDER = RealGoogleProvider() if os.environ.get("GOOGLE_MODE") == "real" else MockGoogleProvider()
    return _PROVIDER
