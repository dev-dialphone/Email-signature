// Gmail content script: detect a compose window, resolve the logged-in
// employee's entity signature from the backend, inject it once per compose.
//
// ponytail: relies on Gmail's DOM. The compose body is the editable region
// 'div[aria-label="Message Body"]' (with contenteditable / g_editable
// fallbacks). No public API exists for compose injection, so DOM is the only
// route. Verbose console logs (prefix [EntitySig]) make failures diagnosable.

const DEFAULT_API = "https://edf21d59737b4fd391d05333c29ee474.preview.crownitsolution.com:39000";
const SELECTORS = {
  composeBody: 'div[aria-label="Message Body"], div[g_editable="true"], div[role="textbox"][contenteditable="true"]',
};

let API_BASE = DEFAULT_API;
chrome.storage?.sync?.get?.(["apiBase"], (v) => {
  if (v && v.apiBase) API_BASE = v.apiBase;
  log("backend =", API_BASE);
});

function log(...a) { console.log("[EntitySig]", ...a); }

// The signed-in Gmail address. Gmail puts it in the title and the account
// button's aria-label; try several spots.
function detectEmail() {
  const scan = (s) => (s && s.match(/[\w.+-]+@[\w.-]+\.[a-z]{2,}/i) || [null])[0];
  let e = scan(document.title);
  if (e) return e.toLowerCase();
  for (const sel of ['a[aria-label*="@"]', 'a[href^="https://accounts.google"][aria-label]']) {
    const el = document.querySelector(sel);
    e = el && scan(el.getAttribute("aria-label"));
    if (e) return e.toLowerCase();
  }
  return null;
}

let cachedHtml = null, cachedEmail = null;
async function fetchSignature(email) {
  if (cachedEmail === email && cachedHtml !== null) return cachedHtml;
  try {
    const res = await fetch(`${API_BASE}/api/resolve?email=${encodeURIComponent(email)}`);
    const data = await res.json();
    log("resolve", email, "->", data.found ? "found" : ("NOT found: " + (data.reason || "")));
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

async function injectInto(body) {
  if (!body || alreadyInjected(body)) return;
  const email = detectEmail();
  if (!email) { log("could not detect your Gmail address"); return; }
  const html = await fetchSignature(email);
  if (!html) return;
  if (alreadyInjected(body)) return;
  const wrap = document.createElement("div");
  wrap.setAttribute("data-entity-sig", "1");
  wrap.innerHTML = `<br><br>${html}`;
  body.appendChild(wrap);
  log("signature injected into compose ✓");
}

function scan() {
  document.querySelectorAll(SELECTORS.composeBody).forEach((body) => {
    if (!alreadyInjected(body)) injectInto(body);
  });
}

// Watch for compose windows opening.
new MutationObserver(scan).observe(document.body, { childList: true, subtree: true });
// And poll for a few seconds after load (compose may already be open / SPA nav).
let ticks = 0;
const iv = setInterval(() => { scan(); if (++ticks > 20) clearInterval(iv); }, 500);
scan();
log("content script loaded");
