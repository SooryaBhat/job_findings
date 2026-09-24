const appListEl = document.getElementById("appList");
const statusFilter = document.getElementById("statusFilter");

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

function renderApps(rows) {
  if (!rows.length) {
    appListEl.innerHTML = `<div class="empty-state">Nothing here yet.</div>`;
    return;
  }
  appListEl.innerHTML = rows.map(job => `
    <div class="card" data-id="${job.id}">
      <div class="card-top">
        <div>
          <h3>${job.title}</h3>
          <div class="company">${job.company_name} · ${job.location || ""} · Applied ${fmtDate(job.applied_at)}</div>
        </div>
        <div class="score-badge score-mid">${job.fit_score}</div>
      </div>
      <div class="actions">
        <button class="subtle" onclick="window.open('${job.application_url}', '_blank')">Open Posting</button>
        <select onchange="updateStatus('${job.id}', this.value)">
          <option value="applied" ${job.status === "applied" ? "selected" : ""}>Applied</option>
          <option value="interviewing" ${job.status === "interviewing" ? "selected" : ""}>Interviewing</option>
          <option value="offer" ${job.status === "offer" ? "selected" : ""}>Offer</option>
          <option value="rejected" ${job.status === "rejected" ? "selected" : ""}>Rejected</option>
        </select>
      </div>
      <textarea placeholder="Follow-up notes (next round date, recruiter name, etc.)"
                onchange="updateNotes('${job.id}', this.value)"
                style="width:100%; margin-top:10px; min-height:50px;">${job.followup_notes || ""}</textarea>
    </div>
  `).join("");
}

async function loadApps() {
  appListEl.innerHTML = `<div class="empty-state">Loading…</div>`;
  const { data, error } = await sb.from("jobs")
    .select("*")
    .eq("status", statusFilter.value)
    .order("applied_at", { ascending: false });
  if (error) {
    appListEl.innerHTML = `<div class="empty-state">Error: ${error.message}</div>`;
    return;
  }
  renderApps(data);
}

async function updateStatus(id, status) {
  await sb.from("jobs").update({ status }).eq("id", id);
  loadApps();
}

async function updateNotes(id, notes) {
  await sb.from("jobs").update({ followup_notes: notes }).eq("id", id);
}

statusFilter.addEventListener("change", loadApps);
loadApps();
