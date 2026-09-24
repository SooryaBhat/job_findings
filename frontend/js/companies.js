const companyRows = document.getElementById("companyRows");
const searchCompInput = document.getElementById("searchCompInput");
const filterTier = document.getElementById("filterTier");
const filterStatus = document.getElementById("filterStatus");

const statTotalComp = document.getElementById("statTotalComp");
const statWorkingComp = document.getElementById("statWorkingComp");
const statReviewComp = document.getElementById("statReviewComp");
const statActiveComp = document.getElementById("statActiveComp");

const editModal = document.getElementById("editModal");

let allCompanies = [];

function fmtDate(iso) {
  if (!iso) return "never";
  return new Date(iso).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

function statusBadge(status) {
  const map = {
    working: '<span class="badge status-working">✅ Working</span>',
    needs_review: '<span class="badge status-needs_review">⚠️ Needs Review</span>',
    failed: '<span class="badge status-failed">❌ Failed</span>',
    pending: '<span class="badge status-needs_review">⏳ Pending</span>',
  };
  return map[status] || `<span class="badge status-unsupported">${status || 'unknown'}</span>`;
}

function tierBadge(tier) {
  const map = {
    dream: '<span class="badge tier-reach">⭐ Dream</span>',
    high_priority: '<span class="badge tier-reach">🔥 High Priority</span>',
    good: '<span class="badge tier-competitive">🎯 Good</span>',
    startup: '<span class="badge tier-achievable">🚀 Startup</span>',
    backup: '<span class="badge track-other">📦 Backup</span>',
  };
  return map[tier] || `<span class="badge track-other">${tier || 'good'}</span>`;
}

function updateCompanyStats(list) {
  statTotalComp.textContent = list.length;
  statWorkingComp.textContent = list.filter(c => c.status === "working").length;
  statReviewComp.textContent = list.filter(c => c.status === "needs_review" || c.ats === "unknown" || c.ats === "custom").length;
  statActiveComp.textContent = list.filter(c => c.active).length;
}

function renderCompanyTable(list) {
  if (!list.length) {
    companyRows.innerHTML = `<tr><td colspan="9" class="empty-state">No companies found matching filters.</td></tr>`;
    return;
  }

  companyRows.innerHTML = list.map(c => `
    <tr>
      <td>
        <strong>${escapeHtml(c.name)}</strong>
        ${c.website ? `<br/><a href="${escapeHtml(c.website)}" target="_blank" style="color: #38bdf8; font-size: 11px;">🌐 Website</a>` : ""}
      </td>
      <td>${tierBadge(c.tier)}</td>
      <td>
        <strong>${escapeHtml(c.ats || 'unknown')}</strong>
        ${c.ats_identifier ? `<br/><span style="color: #94a3b8; font-size: 11px;">ID: ${escapeHtml(c.ats_identifier)}</span>` : ""}
      </td>
      <td>
        ${c.careers_url ? `<a href="${escapeHtml(c.careers_url)}" target="_blank" style="color: #38bdf8;">🔗 Careers Link</a>` : '<span style="color: #94a3b8;">No link</span>'}
      </td>
      <td>${statusBadge(c.status)}</td>
      <td><strong>${c.jobs_found_count || 0}</strong></td>
      <td>${fmtDate(c.last_checked_at)}</td>
      <td>
        <input type="checkbox" ${c.active ? "checked" : ""} onchange="toggleActive('${c.id}', this.checked)" />
      </td>
      <td>
        <button class="subtle" style="padding: 4px 8px; font-size: 12px;" onclick="detectAts('${c.id}', '${escapeJs(c.careers_url)}')">🔍 Detect</button>
        <button class="subtle" style="padding: 4px 8px; font-size: 12px;" onclick="openEditModal('${c.id}')">✏️ Edit</button>
        <button class="danger" style="padding: 4px 8px; font-size: 12px;" onclick="deleteCompany('${c.id}', '${escapeJs(c.name)}')">🗑️</button>
      </td>
    </tr>
  `).join("");
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function escapeJs(str) {
  if (!str) return "";
  return String(str).replace(/'/g, "\\'");
}

async function loadCompanies() {
  companyRows.innerHTML = `<tr><td colspan="9" class="empty-state">Loading company list from Supabase...</td></tr>`;
  
  const { data, error } = await sb.from("companies").select("*").order("created_at", { ascending: false });
  if (error) {
    companyRows.innerHTML = `<tr><td colspan="9" class="empty-state">Error: ${escapeHtml(error.message)}</td></tr>`;
    return;
  }

  allCompanies = data || [];
  updateCompanyStats(allCompanies);
  filterAndRenderCompanies();
}

function filterAndRenderCompanies() {
  let list = allCompanies;
  const search = searchCompInput.value.trim().toLowerCase();
  const tier = filterTier.value;
  const status = filterStatus.value;

  if (search) {
    list = list.filter(c => c.name && c.name.toLowerCase().includes(search));
  }
  if (tier !== "all") {
    list = list.filter(c => c.tier === tier);
  }
  if (status !== "all") {
    list = list.filter(c => c.status === status);
  }

  renderCompanyTable(list);
}

async function addCompany() {
  const name = document.getElementById("newName").value.trim();
  const website = document.getElementById("newWebsite").value.trim() || null;
  const careers_url = document.getElementById("newUrl").value.trim() || null;
  const category = document.getElementById("newCategory").value;
  const tier = document.getElementById("newTier").value;
  const ats = document.getElementById("newAts").value;
  const ats_identifier = document.getElementById("newIdent").value.trim() || null;

  if (!name) { alert("Company name is required"); return; }

  let status = "pending";
  if (ats && ats !== "pending") {
    status = (ats === "custom" || ats === "unknown") ? "needs_review" : "working";
  }

  const { error } = await sb.from("companies").insert({
    name, website, careers_url, category, tier, ats, ats_identifier, status, active: true
  });

  if (error) { alert("Error adding company: " + error.message); return; }

  document.getElementById("newName").value = "";
  document.getElementById("newWebsite").value = "";
  document.getElementById("newUrl").value = "";
  document.getElementById("newIdent").value = "";

  loadCompanies();
}

async function toggleActive(id, active) {
  await sb.from("companies").update({ active }).eq("id", id);
  const comp = allCompanies.find(c => c.id === id);
  if (comp) comp.active = active;
  updateCompanyStats(allCompanies);
}

async function deleteCompany(id, name) {
  if (!confirm(`Are you sure you want to delete ${name}?`)) return;
  const { error } = await sb.from("companies").delete().eq("id", id);
  if (error) { alert("Delete error: " + error.message); return; }
  loadCompanies();
}

function detectAts(id, url) {
  if (!url || url === "null" || url === "undefined") {
    alert("Please set a Careers Page URL first!");
    return;
  }

  let ats = "unknown";
  let ident = null;

  if (url.includes("greenhouse.io")) {
    ats = "greenhouse";
    const m = url.match(/(?:boards|job-boards)\.greenhouse\.io\/([a-zA-Z0-9\-_]+)/);
    if (m) ident = m[1];
  } else if (url.includes("lever.co")) {
    ats = "lever";
    const m = url.match(/jobs\.lever\.co\/([a-zA-Z0-9\-_]+)/);
    if (m) ident = m[1];
  } else if (url.includes("ashbyhq.com")) {
    ats = "ashby";
    const m = url.match(/jobs\.ashbyhq\.com\/([a-zA-Z0-9\-_]+)/);
    if (m) ident = m[1];
  } else if (url.includes("myworkdayjobs.com")) {
    ats = "workday";
  } else if (url.includes("smartrecruiters.com")) {
    ats = "smartrecruiters";
  } else {
    ats = "custom";
  }

  const status = (ats === "custom" || ats === "unknown") ? "needs_review" : "working";

  sb.from("companies").update({ ats, ats_identifier: ident, status }).eq("id", id).then(({ error }) => {
    if (error) {
      alert("Detection update failed: " + error.message);
    } else {
      alert(`Platform Detected: ${ats}${ident ? ' (' + ident + ')' : ''}`);
      loadCompanies();
    }
  });
}

function openEditModal(id) {
  const c = allCompanies.find(comp => comp.id === id);
  if (!c) return;

  document.getElementById("editId").value = c.id;
  document.getElementById("editName").value = c.name || "";
  document.getElementById("editCareersUrl").value = c.careers_url || "";
  document.getElementById("editTier").value = c.tier || "good";
  document.getElementById("editAts").value = c.ats || "unknown";
  document.getElementById("editIdent").value = c.ats_identifier || "";

  editModal.style.display = "flex";
}

function closeEditModal() {
  editModal.style.display = "none";
}

async function saveEditCompany() {
  const id = document.getElementById("editId").value;
  const name = document.getElementById("editName").value.trim();
  const careers_url = document.getElementById("editCareersUrl").value.trim() || null;
  const tier = document.getElementById("editTier").value;
  const ats = document.getElementById("editAts").value;
  const ats_identifier = document.getElementById("editIdent").value.trim() || null;

  const status = (ats === "custom" || ats === "unknown") ? "needs_review" : "working";

  const { error } = await sb.from("companies").update({
    name, careers_url, tier, ats, ats_identifier, status
  }).eq("id", id);

  if (error) { alert("Save error: " + error.message); return; }

  closeEditModal();
  loadCompanies();
}

searchCompInput.addEventListener("input", filterAndRenderCompanies);
filterTier.addEventListener("change", filterAndRenderCompanies);
filterStatus.addEventListener("change", filterAndRenderCompanies);

loadCompanies();
