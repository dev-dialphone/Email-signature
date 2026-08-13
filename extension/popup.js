// Popup: set the backend URL and test resolve against the active Gmail tab's
// account email (or a manual probe).
const $ = (s) => document.querySelector(s);
const DEFAULT = "https://signature.crownitsolution.com";

chrome.storage.sync.get(["apiBase"], (v) => { $("#api").value = (v && v.apiBase) || DEFAULT; });

$("#save").onclick = async () => {
  const apiBase = ($("#api").value || DEFAULT).replace(/\/+$/, "");
  chrome.storage.sync.set({ apiBase });
  $("#status").textContent = "Saved. Testing…";

  // Try to read the email from the active Gmail tab's title.
  let email = null;
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const m = tab && tab.title && tab.title.match(/[\w.+-]+@[\w.-]+\.[a-z]{2,}/i);
    if (m) email = m[0].toLowerCase();
  } catch (e) {}

  if (!email) {
    $("#status").textContent = "Saved. Open a Gmail tab to auto-detect your address.";
    return;
  }
  try {
    const res = await fetch(`${apiBase}/api/resolve?email=${encodeURIComponent(email)}`);
    const data = await res.json();
    if (data.found) {
      $("#status").innerHTML = `✓ ${email} → <b>${data.entity}</b>`;
      $("#preview").style.display = "block";
      $("#preview").innerHTML = data.html;
    } else {
      $("#status").textContent = `✗ ${email}: ${data.reason || "not registered"}`;
      $("#preview").style.display = "none";
    }
  } catch (e) {
    $("#status").textContent = "✗ Could not reach backend at " + apiBase;
  }
};
