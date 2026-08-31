// Popup: set the backend URL (+ optional manual email) and test resolve against
// the active Gmail tab's account email or the manual address.
const $ = (s) => document.querySelector(s);
const DEFAULT = "https://signature.crownitsolution.com";

chrome.storage.sync.get(["apiBase", "email"], (v) => {
  $("#api").value = (v && v.apiBase) || DEFAULT;
  if (v && v.email) $("#email").value = v.email;
});

$("#save").onclick = async () => {
  const apiBase = ($("#api").value || DEFAULT).replace(/\/+$/, "");
  const manual = ($("#email").value || "").trim().toLowerCase();
  chrome.storage.sync.set({ apiBase, email: manual });
  $("#status").textContent = "Saved. Testing…";

  // Prefer the manually-entered address; else read from the active Gmail tab title.
  let email = manual || null;
  if (!email) {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const m = tab && tab.title && tab.title.match(/[\w.+-]+@[\w.-]+\.[a-z]{2,}/i);
      if (m) email = m[0].toLowerCase();
    } catch (e) {}
  }

  if (!email) {
    $("#status").textContent = "Saved. Enter your Gmail address above, or open a Gmail tab, then Test.";
    return;
  }
  try {
    const res = await fetch(`${apiBase}/api/resolve?email=${encodeURIComponent(email)}`,
                            { credentials: "omit", cache: "no-store" });
    const ct = res.headers.get("content-type") || "";
    if (!ct.includes("application/json")) {
      $("#status").textContent = `✗ Backend returned ${res.status} (not JSON) — Cloudflare may be blocking /api/*. Whitelist it.`;
      $("#preview").style.display = "none";
      return;
    }
    const data = await res.json();
    if (data.found) {
      $("#status").innerHTML = `✓ ${email} → <b>${data.entity}</b>`;
      $("#preview").style.display = "block";
      $("#preview").innerHTML = data.html;
    } else {
      $("#status").textContent = `✗ ${email}: ${data.reason || "domain not registered"}`;
      $("#preview").style.display = "none";
    }
  } catch (e) {
    $("#status").textContent = "✗ Could not reach backend at " + apiBase;
  }
};
