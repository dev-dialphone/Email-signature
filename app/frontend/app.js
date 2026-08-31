// Vanilla-JS SPA. No build step — one file, hash-free, role-aware.
// ponytail: hand-rolled render loop, fine for this admin tool; swap to React
// (the extracted components) if the UI grows.
const $ = (s, r=document) => r.querySelector(s);
let state = { token: localStorage.getItem('tok'), user: null, tab: 'signature' };

async function api(path, opts={}) {
  const headers = { 'Content-Type':'application/json', ...(opts.headers||{}) };
  if (state.token) headers.Authorization = 'Bearer ' + state.token;
  let res;
  try {
    res = await fetch('/api'+path, { ...opts, headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined });
  } catch (e) {
    throw new Error('Cannot reach the server — is the backend running?');
  }
  if (res.status === 401) { logout(); throw new Error('unauth'); }
  const text = await res.text();
  let data = {};
  try { data = text ? JSON.parse(text) : {}; } catch { /* non-JSON body */ }
  if (!res.ok) throw new Error(data.detail || res.statusText || 'Request failed');
  return res.status === 204 ? null : data;
}
async function upload(path, file) {
  const fd = new FormData(); fd.append('file', file);
  const res = await fetch('/api'+path, { method:'POST',
    headers: state.token ? { Authorization:'Bearer '+state.token } : {}, body: fd });
  const data = await res.json().catch(()=>({}));
  if (!res.ok) throw new Error(data.detail || 'Upload failed');
  return data;
}
function logout(){ state.token=null; state.user=null; localStorage.removeItem('tok'); render(); }

// ---------- Login ----------
function loginView() {
  const app = $('#app');
  app.innerHTML = `<div class="wrap center"><div class="card">
    <h2>Sign in</h2>
    <label>Email</label><input id="e" placeholder="you@company.com"/>
    <label>Password</label>
    <div style="position:relative">
      <input id="p" type="password" style="padding-right:64px"/>
      <button id="peye" type="button" style="position:absolute;right:6px;top:50%;transform:translateY(-50%);
        background:none;border:0;color:var(--accent);cursor:pointer;font-size:12px;padding:4px 8px">Show</button>
    </div>
    <div style="margin-top:14px"><button id="go">Sign in</button></div>
    <p id="err" style="color:#dc2626;font-size:13px"></p></div></div>`;
  $('#peye').onclick = () => {
    const p = $('#p');
    const show = p.type === 'password';
    p.type = show ? 'text' : 'password';
    $('#peye').textContent = show ? 'Hide' : 'Show';
    p.focus();
  };
  $('#p').addEventListener('keydown', e => { if (e.key === 'Enter') $('#go').click(); });
  $('#go').onclick = async () => {
    try {
      const r = await api('/auth/login', { method:'POST',
        body:{ email:$('#e').value, password:$('#p').value }});
      state.token = r.token; state.user = r.user; localStorage.setItem('tok', r.token);
      state.tab = r.user.role === 'owner' ? 'tenants' : 'signature';
      render();
    } catch(e){ $('#err').textContent = e.message; }
  };
}

// ---------- Shell ----------
function shell(body) {
  const tabs = state.user.role === 'owner'
    ? [['tenants','Entities']]
    : [['signature','Signature'],['sigtemplates','Templates'],['directory','Directory'],['promos','Promotions'],['apply','Apply & Status']];
  return `<header><b>Signature Manager</b>
    <span>${state.user.name} · ${state.user.role}
    <button class="sec" style="margin-left:12px" onclick="logout()">Logout</button></span></header>
    <div class="wrap"><div class="tabs">${
      tabs.map(([k,l])=>`<button class="${state.tab===k?'active':''}" onclick="go('${k}')">${l}</button>`).join('')
    }</div>${body}</div>`;
}
window.go = (t) => { state.tab = t; render(); };
window.logout = logout;

// ---------- Owner: entities ----------
let editingTenant = null;   // id of the row currently in edit mode

async function tenantsView() {
  const list = await api('/tenants');
  const rows = list.map(t => {
    if (editingTenant === t.id) {
      return `<tr>
        <td><input id="et-name-${t.id}" value="${t.name}"/></td>
        <td><input id="et-domain-${t.id}" value="${t.domain||''}"/></td>
        <td><button onclick="saveTenant('${t.id}')">Save</button>
          <button class="sec" onclick="cancelEdit()">Cancel</button></td></tr>`;
    }
    return `<tr><td>${t.name}</td><td>${t.domain||''}</td>
      <td><button class="sec" onclick="editTenant('${t.id}')">Edit</button>
        <button class="warn" onclick="removeTenant('${t.id}','${t.name.replace(/'/g,"")}')">Remove</button></td></tr>`;
  }).join('');
  $('#app').innerHTML = shell(`
    <div class="card"><h2>Entities</h2>
      <table><tr><th>Name</th><th>Domain</th><th></th></tr>
        ${rows||'<tr><td colspan=3 class="muted">No entities yet — add one below</td></tr>'}</table></div>
    <div class="card"><h2>Add entity</h2>
      <div class="row"><div><label>Name</label><input id="tn"/></div>
        <div><label>Domain</label><input id="td" placeholder="yourcompany.com"/></div></div>
      <div class="row"><div><label>Admin name</label><input id="an"/></div>
        <div><label>Admin email</label><input id="ae"/></div>
        <div><label>Admin password</label><input id="ap" type="password"/></div></div>
      <div style="margin-top:12px"><button id="add">Create</button>
        <span id="tmsg" class="muted" style="margin-left:10px"></span></div></div>`);
  $('#add').onclick = async () => {
    try {
      await api('/tenants',{method:'POST',body:{name:$('#tn').value,domain:$('#td').value,
        admin_name:$('#an').value,admin_email:$('#ae').value,admin_password:$('#ap').value}});
      render();
    } catch(e){ $('#tmsg').textContent = e.message; }
  };
}
window.editTenant = (id) => { editingTenant = id; tenantsView(); };
window.cancelEdit = () => { editingTenant = null; tenantsView(); };
window.saveTenant = async (id) => {
  await api(`/tenants/${id}`,{method:'PATCH',body:{
    name:$('#et-name-'+id).value, domain:$('#et-domain-'+id).value}});
  editingTenant = null; tenantsView();
};
window.removeTenant = async (id,name) => {
  if (!confirm(`Remove entity "${name}"? This deletes its admin, employees, signature and promos.`)) return;
  await api(`/tenants/${id}`,{method:'DELETE'}); tenantsView();
};

// ---------- Admin: signature ----------
const SIG_FIELDS = [['company_name','Company name'],['tagline','Tagline'],['address','Address'],
  ['website','Website'],['phone','Company phone'],['email','Company email'],
  ['facebook','Facebook URL'],['linkedin','LinkedIn URL'],['instagram','Instagram URL'],
  ['twitter','Twitter/X URL'],['youtube','YouTube URL']];
const LAYOUTS = [
  ['classic','Classic','Two columns: name left, logo + socials right'],
  ['modern','Modern','Logo beside name, accent bar, contact on one line'],
  ['minimal','Minimal','Name · title side by side, small icons, logo right'],
  ['bold','Bold','Thick left accent bar, large name, logo down the right'],
  ['compact','Compact','Two lines only — name·title, phone·email·web'],
  ['stacked','Stacked','Single column, socials by name, logo at bottom'],
  ['stacked_social_bottom','Stacked (social bottom)','Stacked, socials under the logo'],
  ['arranged','Arranged','Custom logo & social placement'],
];

let sigSubTab = 'fields';   // 'fields' | 'design'

// Gather every editable value on the panel into a PATCH body (both sub-tabs are
// in the DOM at once; hidden ones still carry their persisted values).
function collectSig() {
  const body = { enabled: $('#en').value==='1', layout:$('#lay').value,
                 logo_size:$('#ls').value };
  const lp = $('#logo_pos'), sp = $('#social_pos');
  if (lp) body.logo_pos = lp.value;
  if (sp) body.social_pos = sp.value;
  document.querySelectorAll('[data-k]').forEach(i=>body[i.dataset.k]=i.value);
  return body;
}

async function signatureView() {
  const sig = await api('/signature');
  const prev = await api('/signature/preview');
  const fields = SIG_FIELDS.map(([k,l])=>`<div><label>${l}</label>
    <input data-k="${k}" value="${sig[k]||''}"/></div>`).join('');
  const isCustomPx = sig.logo_size && /^\d+$/.test(String(sig.logo_size));
  const pxVal = isCustomPx ? sig.logo_size : 240;

  const fieldsTab = `
    <div class="row" style="margin-bottom:6px">
      <div><label>Signature appended to outgoing mail</label>
        <select id="en"><option value="1"${sig.enabled?' selected':''}>ON</option>
          <option value="0"${!sig.enabled?' selected':''}>OFF</option></select></div>
    </div>
    <label>Logo</label>
    <div class="row"><div><input data-k="logo_url" value="${sig.logo_url||''}" placeholder="Logo URL or upload →"/></div>
      <div style="flex:0 0 auto"><input type="file" id="logof" accept="image/*"/></div></div>
    <div class="row" style="align-items:flex-end">
      <div><label>Logo size</label><select id="ls">
        <option value="small"${sig.logo_size==='small'?' selected':''}>Small (120px)</option>
        <option value="medium"${sig.logo_size==='medium'?' selected':''}>Medium (180px)</option>
        <option value="large"${sig.logo_size==='large'?' selected':''}>Large (240px)</option>
        <option value="__px__"${isCustomPx?' selected':''}>Custom pixels…</option></select></div>
      <div id="pxwrap" style="${isCustomPx?'':'display:none'}">
        <label>Custom width: <span id="pxlbl">${pxVal}</span>px</label>
        <input type="range" id="pxrange" min="60" max="500" value="${pxVal}"/></div>
    </div>
    <div class="row">${fields}</div>`;

  const designTab = `
    <label>Template</label>
    <input type="hidden" id="lay" value="${sig.layout}"/>
    <div class="tpl-grid">${
      LAYOUTS.map(([id,name,desc])=>`
        <div class="tpl ${sig.layout===id?'sel':''}" onclick="pickLayout('${id}')" title="${desc}">
          <div class="tpl-name">${name}</div>
          <div class="tpl-desc">${desc}</div>
        </div>`).join('')}</div>
    ${sig.layout==='arranged'?`
    <div class="row" style="margin-top:12px">
      <div><label>Logo position</label><select id="logo_pos">
        <option value="right"${sig.logo_pos==='right'?' selected':''}>Right</option>
        <option value="below"${sig.logo_pos==='below'?' selected':''}>Below</option></select></div>
      <div><label>Social position</label><select id="social_pos">
        <option value="with_name"${sig.social_pos==='with_name'?' selected':''}>Next to name</option>
        <option value="below_logo"${sig.social_pos==='below_logo'?' selected':''}>Below logo</option>
        <option value="bottom"${sig.social_pos==='bottom'?' selected':''}>At bottom</option></select></div>
    </div>
    <p class="muted">Arranged: pick logo & social placement independently.</p>`:''}`;

  $('#app').innerHTML = shell(`<div class="grid">
    <div class="card">
      <div class="tabs" style="margin-bottom:14px">
        <button class="${sigSubTab==='fields'?'active':''}" onclick="sigTab('fields')">Fields</button>
        <button class="${sigSubTab==='design'?'active':''}" onclick="sigTab('design')">Design</button>
      </div>
      <div style="${sigSubTab==='fields'?'':'display:none'}">${fieldsTab}</div>
      <div style="${sigSubTab==='design'?'':'display:none'}">${designTab}</div>
      <div style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap">
        <button id="save">Save</button>
        <button class="sec" id="test">Send test email</button>
        <button class="sec" id="astpl">Save as Template</button>
        <button class="sec" id="copygm">Copy for Gmail</button>
        <button class="sec" id="dlhtml">Download .html</button>
        <button class="sec" id="dlimg">Download image</button>
        <span id="msg" class="muted" style="align-self:center"></span></div>
    </div>
    <div class="card"><h2>Live preview <span class="muted">(your identity as sample)</span></h2>
      <div class="preview">${prev.html}</div>
      <p class="muted">Company parts are shared; {{AGENT_NAME}} / {{AGENT_EMAIL}} etc. fill per person at send.</p>
      <div id="testbox"></div>
    </div></div>`);

  // keep hidden sub-tab's inputs from being lost: both are in the DOM already.
  const ls = $('#ls'), pxwrap = $('#pxwrap');
  if (ls) ls.onchange = () => { pxwrap.style.display = ls.value==='__px__' ? '' : 'none'; };
  const pxr = $('#pxrange');
  if (pxr) pxr.oninput = () => { $('#pxlbl').textContent = pxr.value; };

  $('#logof') && ($('#logof').onchange = async (e) => {
    const f = e.target.files[0]; if (!f) return;
    $('#msg').textContent = 'Uploading logo…';
    try { const r = await upload('/signature/logo', f);
      $('[data-k="logo_url"]').value = r.url; $('#msg').textContent='Logo uploaded ✓'; signatureView(); }
    catch(err){ $('#msg').textContent = err.message; }
  });
  $('#save').onclick = async () => {
    const body = collectSig();
    if ($('#ls') && $('#ls').value==='__px__') body.logo_size = $('#pxrange').value;
    await api('/signature',{method:'PATCH',body});
    $('#msg').textContent='Saved ✓'; signatureView();
  };
  $('#test').onclick = async () => {
    $('#msg').textContent='Sending test…';
    const r = await api('/signature/test',{method:'POST'});
    $('#msg').textContent = `Test → ${r.sent_to}`;
    $('#testbox').innerHTML = `<div class="card" style="margin-top:12px"><h2>Test email body</h2>
      <p class="muted">${r.note}</p><div class="preview">${r.html}</div></div>`;
  };
  $('#astpl').onclick = async () => {
    const name = prompt('Template name?'); if (!name) return;
    await api('/signature',{method:'PATCH',body:collectSig()});   // save current first
    await api('/sig-templates',{method:'POST',body:{name}});
    $('#msg').textContent='Saved as template ✓';
  };
  // Copy-for-Gmail: put the RENDERED signature (not the HTML source) on the
  // clipboard as rich text, so pasting into Gmail's signature box keeps logo,
  // colours and layout — exactly how signature-maker sites work.
  $('#copygm').onclick = async () => {
    $('#msg').textContent='Preparing…';
    await api('/signature',{method:'PATCH',body:collectSig()});   // export current design
    const r = await api('/signature/export');
    try {
      await navigator.clipboard.write([new ClipboardItem({
        'text/html': new Blob([r.html], {type:'text/html'}),
        'text/plain': new Blob([r.html], {type:'text/plain'}),
      })]);
      $('#msg').textContent='Copied ✓ — paste into Gmail → Settings → Signature';
    } catch(e) {   // clipboard API blocked (non-HTTPS/old browser): fall back to download
      $('#msg').textContent='Copy blocked — use Download .html instead';
    }
  };
  $('#dlhtml').onclick = async () => {
    await api('/signature',{method:'PATCH',body:collectSig()});
    const r = await api('/signature/export');
    const blob = new Blob([r.document], {type:'text/html'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = 'email-signature.html'; a.click();
    URL.revokeObjectURL(a.href);
    $('#msg').textContent='Downloaded — open it, select all, copy into Gmail';
  };
  $('#dlimg').onclick = async () => {
    await api('/signature',{method:'PATCH',body:collectSig()});
    const r = await api('/signature/export');
    $('#msg').textContent='Rendering image…';
    try { await sigHtmlToPng(r.html, 'email-signature.png');
      $('#msg').textContent='Image downloaded (use HTML for Gmail — image has no clickable links)'; }
    catch(e){ $('#msg').textContent='Image render failed'; }
  };
}
window.sigTab = (t) => { sigSubTab = t; signatureView(); };
// Clicking a template tile: persist current edits, save the layout, re-render.
window.pickLayout = async (id) => {
  const body = collectSig(); body.layout = id;
  await api('/signature',{method:'PATCH',body});
  sigSubTab = 'design'; signatureView();
};

// ---------- Admin: saved template gallery ----------
async function sigTemplatesView() {
  const tpls = await api('/sig-templates');
  const cards = tpls.map(t=>`<tr><td>${t.name}</td>
    <td><button class="sec" onclick="applyTpl('${t.id}')">Apply</button>
      <button class="warn" onclick="delTpl('${t.id}')">Delete</button></td></tr>`).join('');
  $('#app').innerHTML = shell(`
    <div class="card"><h2>Saved signature designs</h2>
      <table><tr><th>Name</th><th></th></tr>
        ${cards||'<tr><td colspan=2 class="muted">None yet — design a signature then “Save as Template”.</td></tr>'}</table>
      <p class="muted">Apply overwrites the current signature design with the saved one.</p>
      <p id="tplmsg" class="muted"></p></div>`);
}
window.applyTpl = async (id) => {
  const msg = document.getElementById('tplmsg');
  if (msg) msg.textContent = 'Applying…';
  try {
    await api(`/sig-templates/${id}/apply`, { method: 'POST' });
    if (msg) msg.textContent = '✓ Applied. Opening Signature tab…';
    setTimeout(() => { state.tab = 'signature'; render(); }, 600);
  } catch (e) {
    if (msg) msg.textContent = '✗ Could not apply: ' + e.message;
    else alert('Could not apply template: ' + e.message);
  }
};
window.delTpl = async (id) => { await api(`/sig-templates/${id}`,{method:'DELETE'}); sigTemplatesView(); };

// ---------- Admin: directory (employees) ----------
async function directoryView() {
  const emps = await api('/employees');
  const rows = emps.map(e=>`<tr><td>${e.name}</td><td>${e.email}</td><td>${e.title||''}</td>
    <td>${e.phone||''}</td>
    <td style="white-space:nowrap">
      <button class="sec" onclick="copyEmpSig('${e.id}',this)">Copy for Gmail</button>
      <button class="sec" onclick="dlEmpSig('${e.id}','${e.email}')">HTML</button>
      <button class="sec" onclick="imgEmpSig('${e.id}','${e.email}',this)">Image</button>
      <button class="warn" onclick="delEmp('${e.id}')">Remove</button></td></tr>`).join('');
  $('#app').innerHTML = shell(`
    <div class="card"><h2>Employees (who receives the signature)</h2>
      <table><tr><th>Name</th><th>Email</th><th>Title</th><th>Phone</th><th></th></tr>
        ${rows||'<tr><td colspan=5 class="muted">No employees yet — add them below</td></tr>'}</table>
      <p class="muted">Each employee's own name & email are stamped into the signature.
        <b>Copy for Gmail</b>/<b>Download</b> gives THAT agent a ready-to-paste copy —
        share it, they paste into Gmail → Settings → Signature (no editing needed).</p></div>
    <div class="card"><h2>Add employee</h2>
      <div class="row"><div><label>Name</label><input id="en2"/></div>
        <div><label>Email</label><input id="ee" placeholder="person@yourdomain.com"/></div></div>
      <div class="row"><div><label>Title</label><input id="et"/></div>
        <div><label>Phone</label><input id="ep"/></div></div>
      <div style="margin-top:12px"><button id="ea">Add</button>
        <span id="emsg" class="muted" style="margin-left:10px"></span></div></div>`);
  $('#ea').onclick = async () => {
    try {
      await api('/employees',{method:'POST',body:{name:$('#en2').value,email:$('#ee').value,
        title:$('#et').value,phone:$('#ep').value}});
      directoryView();
    } catch(e){ $('#emsg').textContent = e.message; }
  };
}
window.delEmp = async (id) => { await api(`/employees/${id}`,{method:'DELETE'}); directoryView(); };

// Render signature HTML to a PNG in the browser (no server/headless needed).
// Off-screen node, wait for images (logo/banner) to load, then snapshot.
async function sigHtmlToPng(html, filename) {
  const holder = document.createElement('div');
  holder.style.cssText = 'position:fixed;left:-9999px;top:0;background:#fff;padding:12px;display:inline-block';
  holder.innerHTML = html;
  document.body.appendChild(holder);
  try {
    await Promise.all([...holder.querySelectorAll('img')].map(img =>
      img.complete ? Promise.resolve()
        : new Promise(r => { img.onload = img.onerror = r; })));
    const url = await htmlToImage.toPng(holder, {pixelRatio: 2, backgroundColor: '#ffffff'});
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
  } finally { holder.remove(); }
}
// Per-agent export: renders the signature with THAT agent's real identity, so
// each agent gets a ready-to-paste copy (no placeholders to edit).
window.copyEmpSig = async (id, btn) => {
  const old = btn.textContent; btn.textContent = '…';
  try {
    const r = await api(`/signature/export?employee_id=${id}`);
    await navigator.clipboard.write([new ClipboardItem({
      'text/html': new Blob([r.html], {type:'text/html'}),
      'text/plain': new Blob([r.html], {type:'text/plain'}),
    })]);
    btn.textContent = 'Copied ✓';
  } catch(e){ btn.textContent = 'Copy blocked — use Download'; }
  setTimeout(()=>{ btn.textContent = old; }, 2500);
};
window.dlEmpSig = async (id, email) => {
  const r = await api(`/signature/export?employee_id=${id}`);
  const blob = new Blob([r.document], {type:'text/html'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `signature-${email.replace(/[^a-z0-9]+/gi,'_')}.html`; a.click();
  URL.revokeObjectURL(a.href);
};
window.imgEmpSig = async (id, email, btn) => {
  const old = btn.textContent; btn.textContent = '…';
  try {
    const r = await api(`/signature/export?employee_id=${id}`);
    await sigHtmlToPng(r.html, `signature-${email.replace(/[^a-z0-9]+/gi,'_')}.png`);
    btn.textContent = old;
  } catch(e){ btn.textContent = 'Image failed'; setTimeout(()=>btn.textContent=old,2000); }
};

// ---------- Admin: promotions ----------
async function promosView() {
  const promos = await api('/promos');
  const rows = promos.map(p=>`<tr><td>${p.name}</td><td>${p.position}</td>
    <td>${p.active?'<span class="badge ok">active</span>':'<span class="badge">off</span>'}</td>
    <td>${p.active?`<button class="sec" onclick="promo('${p.id}','deactivate')">Deactivate</button>`
      :`<button class="sec" onclick="promo('${p.id}','activate')">Activate</button>`}
      <button class="warn" onclick="delPromo('${p.id}')">Delete</button></td></tr>`).join('');
  $('#app').innerHTML = shell(`
    <div class="card"><h2>Event / promotional banners</h2>
      <table><tr><th>Name</th><th>Position</th><th>Status</th><th></th></tr>${rows||'<tr><td colspan=4 class="muted">None yet</td></tr>'}</table>
      <p class="muted">One active banner at a time; injected ${'{above|below}'} the signature on next Apply.</p></div>
    <div class="card"><h2>New banner</h2>
      <label>Name</label><input id="pn"/>
      <label>Position</label><select id="pp"><option value="above">Above signature</option><option value="below">Below signature</option></select>
      <label>Upload a ready-made banner image (PNG/JPG/GIF)</label>
      <input type="file" id="pf" accept="image/*"/>
      <label>…or paste an online image URL</label>
      <input id="purl" placeholder="https://your-host.com/banner.png"/>
      <p class="muted">Must be a public, direct image link (opens the image itself in a browser).
        A GitHub <code>blob</code> link is auto-converted to its raw link.</p>
      <div id="pprev" class="preview" style="display:none;margin-top:10px"></div>
      <div style="margin-top:12px"><button id="pc">Create</button>
        <button class="sec" id="ppreviewbtn" type="button" style="margin-left:8px">Preview</button>
        <span id="pmsg" class="muted" style="margin-left:10px"></span></div></div>`);

  // Normalize a pasted URL into an email-safe <img> banner. Returns '' if invalid.
  function urlToBanner(raw) {
    let u = (raw || '').trim();
    if (!/^https?:\/\/\S+$/i.test(u)) return '';
    u = u.replace('https://github.com/', 'https://raw.githubusercontent.com/')
         .replace('/blob/', '/').replace(/\?raw=true$/i, '');
    const esc = u.replace(/"/g, '&quot;');
    return `<div style="padding:8px 0;"><img src="${esc}" alt="promotion" style="max-width:600px;width:100%;display:block;" /></div>`;
  }

  let uploadedHtml = '';   // set when a file is uploaded (takes precedence)

  $('#pf').onchange = async (e) => {
    const f = e.target.files[0]; if (!f) return;
    $('#pmsg').textContent = 'Uploading…';
    try {
      const r = await upload('/promos/upload', f);
      uploadedHtml = r.html;
      $('#pprev').style.display='block'; $('#pprev').innerHTML = r.html;
      $('#pmsg').textContent = 'Image uploaded ✓ — name it and Create';
    } catch(err){ $('#pmsg').textContent = err.message; }
  };

  $('#ppreviewbtn').onclick = () => {
    const html = uploadedHtml || urlToBanner($('#purl').value);
    if (!html) { $('#pmsg').textContent = 'Upload a file or enter a valid image URL first'; return; }
    $('#pprev').style.display='block'; $('#pprev').innerHTML = html;
    $('#pmsg').textContent = 'Preview shown — if the image appears here it will work in email';
  };

  $('#pc').onclick = async () => {
    const html = uploadedHtml || urlToBanner($('#purl').value);
    if (!html) { $('#pmsg').textContent='Upload a file or enter a valid public image URL first'; return; }
    await api('/promos',{method:'POST',body:{name:$('#pn').value||'Banner',html,position:$('#pp').value}});
    promosView();
  };
}
window.promo = async (id,act) => { await api(`/promos/${id}/${act}`,{method:'POST'}); promosView(); };
window.delPromo = async (id) => { await api(`/promos/${id}`,{method:'DELETE'}); promosView(); };

// ---------- Admin: apply & status ----------
async function applyView() {
  const dir = await api('/directory').catch(()=>[]);
  const log = await api('/sync-log').catch(()=>[]);
  const dirRows = dir.map(u=>`<tr><td>${u.name}</td><td>${u.email}</td><td>${u.title||''}</td>
    <td style="white-space:nowrap">
      <button class="sec" onclick="copyMailSig('${u.email}',this)">Copy for Gmail</button>
      <button class="sec" onclick="dlMailSig('${u.email}')">HTML</button>
      <button class="sec" onclick="imgMailSig('${u.email}',this)">Image</button></td></tr>`).join('');
  const logRows = log.map(l=>`<tr><td>${l.user_email}</td>
    <td><span class="badge ${l.status==='ok'?'ok':'err'}">${l.status}</span></td>
    <td class="muted">${l.detail||''}</td>
    <td style="white-space:nowrap">
      <button class="sec" onclick="viewSig('${l.user_email}')">view</button>
      <button onclick="exportMailSig('${l.user_email}',this)">Export</button></td></tr>`).join('');
  $('#app').innerHTML = shell(`
    <div class="card"><h2>Recipients</h2>
      <table><tr><th>Name</th><th>Email</th><th>Title</th><th>Export for Gmail</th></tr>${dirRows||'<tr><td colspan=4 class="muted">No employees — add them in the Directory tab</td></tr>'}</table>
      <div style="margin-top:14px"><button id="apply">Apply signature to everyone</button>
        <span id="am" class="muted" style="margin-left:10px"></span></div></div>
    <div class="card"><h2>Last sync status</h2>
      <table><tr><th>User</th><th>Status</th><th>Detail</th><th></th></tr>${logRows||'<tr><td colspan=4 class="muted">Not applied yet</td></tr>'}</table></div>
    <div id="sigbox"></div>`);
  $('#apply').onclick = async () => {
    $('#am').textContent='Applying…';
    try {
      const r = await api('/apply',{method:'POST'});
      if (r.skipped) { $('#am').textContent = '⚠ ' + r.skipped + ' — turn the signature ON in the Signature tab.'; return; }
      if (!r.total)  { $('#am').textContent = '⚠ No employees yet — add them in the Directory tab.'; return; }
      $('#am').textContent = `Applied to ${r.applied}/${r.total}`; applyView();
    } catch(e){ $('#am').textContent = 'Error: ' + e.message; }
  };
}
window.viewSig = async (email) => {
  const r = await api('/verify/'+encodeURIComponent(email));
  $('#sigbox').innerHTML = `<div class="card"><h2>${email} — applied signature</h2>
    <div class="preview">${r.html||'<span class="muted">nothing applied</span>'}</div>
    <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
      <button class="sec" onclick="copyMailSig('${email}',this)">Copy for Gmail</button>
      <button class="sec" onclick="dlMailSig('${email}')">Download .html</button>
      <button class="sec" onclick="imgMailSig('${email}',this)">Download image</button></div></div>`;
  $('#sigbox').scrollIntoView({behavior:'smooth'});
};

// Export any recipient's signature by email (uses their stored record if listed,
// else a name derived from the address). HTML = correct for Gmail; image = picture only.
const _fn = (email) => 'signature-' + email.replace(/[^a-z0-9]+/gi,'_');
window.copyMailSig = async (email, btn) => {
  const old = btn.textContent; btn.textContent = '…';
  try {
    const r = await api('/signature/export?email='+encodeURIComponent(email));
    await navigator.clipboard.write([new ClipboardItem({
      'text/html': new Blob([r.html], {type:'text/html'}),
      'text/plain': new Blob([r.html], {type:'text/plain'}),
    })]);
    btn.textContent = 'Copied ✓';
  } catch(e){ btn.textContent = 'Copy blocked — use HTML'; }
  setTimeout(()=>{ btn.textContent = old; }, 2500);
};
window.dlMailSig = async (email) => {
  const r = await api('/signature/export?email='+encodeURIComponent(email));
  const blob = new Blob([r.document], {type:'text/html'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = _fn(email)+'.html'; a.click();
  URL.revokeObjectURL(a.href);
};
// One-click Export: downloads BOTH the clickable HTML (for pasting into Gmail)
// AND a PNG visual reference, per employee.
window.exportMailSig = async (email, btn) => {
  const old = btn.textContent; btn.textContent = 'Exporting…'; btn.disabled = true;
  try {
    const r = await api('/signature/export?email='+encodeURIComponent(email));
    // 1) HTML file (clickable — the one they paste into Gmail)
    const blob = new Blob([r.document], {type:'text/html'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = _fn(email)+'.html'; a.click();
    URL.revokeObjectURL(a.href);
    // 2) PNG preview (visual reference)
    await sigHtmlToPng(r.html, _fn(email)+'.png');
    btn.textContent = 'Exported ✓';
  } catch(e){ btn.textContent = 'Export failed'; }
  setTimeout(()=>{ btn.textContent = old; btn.disabled = false; }, 2500);
};
window.imgMailSig = async (email, btn) => {
  const old = btn.textContent; btn.textContent = '…';
  try {
    const r = await api('/signature/export?email='+encodeURIComponent(email));
    await sigHtmlToPng(r.html, _fn(email)+'.png');
    btn.textContent = old;
  } catch(e){ btn.textContent = 'Image failed'; setTimeout(()=>btn.textContent=old,2000); }
};

// ---------- Router ----------
const OWNER_TABS = ['tenants'];
const ADMIN_TABS = ['signature','sigtemplates','directory','promos','apply'];

async function render() {
  if (!state.token) return loginView();
  if (!state.user) {
    try { state.user = await api('/auth/me'); }
    catch { return logout(); }   // stale/invalid token → back to login, not blank
  }
  // Force a tab the current role is allowed to see (a persisted owner session
  // must never land on an admin-only view, which 403s and renders blank).
  const allowed = state.user.role === 'owner' ? OWNER_TABS : ADMIN_TABS;
  if (!allowed.includes(state.tab)) state.tab = allowed[0];
  const views = { tenants:tenantsView, signature:signatureView, sigtemplates:sigTemplatesView,
                  directory:directoryView, promos:promosView, apply:applyView };
  try {
    await (views[state.tab] || (() => {}))();
  } catch(e) {
    console.error(e);
    $('#app').innerHTML = shell(`<div class="card"><h2>Something went wrong</h2>
      <p style="color:#dc2626">${e.message}</p>
      <button class="sec" onclick="render()">Retry</button></div>`);
  }
}
window.render = render;
render();
