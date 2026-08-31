// Gmail content script: detect a compose window, resolve the logged-in
// employee's entity signature from the backend, inject it once per compose.
//
// ponytail: relies on Gmail's DOM. The compose body is the editable region
// 'div[aria-label="Message Body"]' (with contenteditable / g_editable
// fallbacks). No public API exists for compose injection, so DOM is the only
// route. Verbose console logs (prefix [EntitySig]) make failures diagnosable.

const DEFAULT_API = "https://signature.crownitsolution.com";
const SELECTORS = {
  // Broadened: Gmail ships several compose DOM variants. Match any editable
  // message body; injectInto() guards against non-compose editables.
  composeBody: 'div[aria-label="Message Body"], div[g_editable="true"], '
             + 'div[role="textbox"][contenteditable="true"], '
             + 'div[contenteditable="true"][aria-label*="essage"]',
};

let API_BASE = DEFAULT_API;
chrome.storage?.sync?.get?.(["apiBase"], (v) => {
  if (v && v.apiBase) API_BASE = v.apiBase;
  log("backend =", API_BASE);
});

function log(...a) { console.log("[EntitySig]", ...a); }

// The signed-in Gmail address. Gmail exposes it in several spots depending on
// the UI build; try them all, then fall back to a manually-set address.
function detectEmail() {
  const scan = (s) => (s && s.match(/[\w.+-]+@[\w.-]+\.[a-z]{2,}/i) || [null])[0];
  // 1) page title  2) account switcher aria-labels  3) any mailto on the page
  let e = scan(document.title);
  if (e) return e.toLowerCase();
  const sels = [
    'a[aria-label*="@"]',
    'a[href^="https://accounts.google"][aria-label]',
    '[aria-label*="Google Account"]',
    'header [aria-label*="@"]',
    'img[aria-label*="@"]',
  ];
  for (const sel of sels) {
    for (const el of document.querySelectorAll(sel)) {
      e = scan(el.getAttribute("aria-label")) || scan(el.getAttribute("title"));
      if (e) return e.toLowerCase();
    }
  }
  // 4) whole-document sweep for a gmail-ish address (last resort)
  e = scan(document.body && document.body.innerText);
  if (e) return e.toLowerCase();
  return MANUAL_EMAIL || null;
}

// Optional manual override (set from the popup) for cases where Gmail hides the
// address (e.g. some Workspace builds). Read once at load.
let MANUAL_EMAIL = null;
chrome.storage?.sync?.get?.(["email"], (v) => { if (v && v.email) MANUAL_EMAIL = v.email.toLowerCase(); });

let cachedHtml = null, cachedEmail = null;
async function fetchSignature(email) {
  if (cachedEmail === email && cachedHtml !== null) return cachedHtml;
  try {
    const res = await fetch(`${API_BASE}/api/resolve?email=${encodeURIComponent(email)}`,
                            { credentials: "omit", cache: "no-store" });
    const ct = res.headers.get("content-type") || "";
    if (!ct.includes("application/json")) {
      // Cloudflare/proxy served an HTML challenge or error page instead of JSON.
      log("resolve BLOCKED: backend returned", res.status, ct,
          "— likely Cloudflare challenge or wrong URL. Whitelist /api/* in Cloudflare.");
      return null;
    }
    const data = await res.json();
    log("resolve", email, "->", data.found ? "found ✓" : ("NOT found: " + (data.reason || "domain not registered")));
    cachedEmail = email;
    cachedHtml = data.found ? data.html : null;
    return cachedHtml;
  } catch (e) {
    log("resolve FAILED (backend unreachable / CORS):", e.message);
    return null;
  }
}

function alreadyInjected(body) {
  return body.querySelector('[data-entity-sig="1"]') !== null;
}

// A body is a real compose area only if it's editable and reasonably sized /
// visible — avoids injecting into search boxes or chat.
function isComposeBody(body) {
  if (!body || body.getAttribute("contenteditable") === "false") return false;
  const r = body.getBoundingClientRect();
  return r.width > 150 && r.height > 40;
}

async function injectInto(body) {
  if (!body || !isComposeBody(body) || alreadyInjected(body)) return;
  const email = detectEmail();
  if (!email) { log("could not detect your Gmail address — set it in the extension popup"); return; }
  const html = await fetchSignature(email);
  if (!html) return;
  if (alreadyInjected(body)) return;
  const wrap = document.createElement("div");
  wrap.setAttribute("data-entity-sig", "1");
  wrap.innerHTML = `<br><br>${html}`;
  body.appendChild(wrap);
  log("signature injected into compose ✓", email);
}

function scan() {
  document.querySelectorAll(SELECTORS.composeBody).forEach((body) => {
    if (!alreadyInjected(body)) injectInto(body);
  });
}

// Watch for compose windows opening (and Gmail re-rendering the body).
new MutationObserver(scan).observe(document.body, { childList: true, subtree: true });
// Poll for a while after load: compose may already be open, the address may
// appear late, and Gmail SPA-navigates without full reloads.
let ticks = 0;
const iv = setInterval(() => { scan(); if (++ticks > 40) clearInterval(iv); }, 500);
scan();
log("content script loaded");
