const jobListEl = document.getElementById("jobList");
const searchInput = document.getElementById("searchInput");
const trackFilter = document.getElementById("trackFilter");
const tierFilter = document.getElementById("tierFilter");
const minScoreEl = document.getElementById("minScore");
const locFilter = document.getElementById("locFilter");
const refreshBtn = document.getElementById("refreshBtn");

const statTotalJobs = document.getElementById("statTotalJobs");
const statHighMatch = document.getElementById("statHighMatch");
const statAiJobs = document.getElementById("statAiJobs");
const statBlrJobs = document.getElementById("statBlrJobs");

const TIER_LABEL = { reach: "🎯 Reach", competitive: "⚖️ Competitive", achievable: "✅ Achievable" };
const TRACK_LABEL = { ai_ml_ds: "⚡ AI/ML/DS", software: "💻 Software", data_analyst: "📊 Data Analyst", other: "Other" };

function scoreClass(score) {
  if (score >= 85) return "score-high";
  if (score >= 65) return "score-mid";
  return "score-low";
}

function timeAgo(iso) {
  if (!iso) return "recently";
  const diffMs = Date.now() - new Date(iso).getTime();
  const hours = Math.floor(diffMs / 3600000);
  if (hours < 1) return "just now";
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function updateStats(allJobs) {
  statTotalJobs.textContent = allJobs.length;
  statHighMatch.textContent = allJobs.filter(j => (j.fit_score || 0) >= 85).length;
  statAiJobs.textContent = allJobs.filter(j => j.track === "ai_ml_ds").length;
  statBlrJobs.textContent = allJobs.filter(j => j.location_priority === 1 || (j.location && (j.location.toLowerCase().includes("bangalore") || j.location.toLowerCase().includes("remote")))).length;
}

function renderJobs(jobs) {
  if (!jobs.length) {
    jobListEl.innerHTML = `<div class="empty-state">No jobs match the current filters.<br/>Try lowering score requirements or clearing search terms.</div>`;
    return;
  }

  jobListEl.innerHTML = jobs.map(job => `
    <div class="card" data-id="${job.id}">
      <div class="card-top">
        <div>
          <h3>${escapeHtml(job.title)}</h3>
          <div class="company">${escapeHtml(job.company_name)} · 📍 ${escapeHtml(job.location || "Location N/A")} · ${timeAgo(job.first_seen_at)}</div>
          <div>
            <span class="badge tier-${job.difficulty_tier}">${TIER_LABEL[job.difficulty_tier] || job.difficulty_tier}</span>
            <span class="badge track-${job.track}">${TRACK_LABEL[job.track] || job.track}</span>
            ${job.source ? `<span class="badge subtle" style="border: 1px solid rgba(255,255,255,0.1); color: #94a3b8;">${escapeHtml(job.source)}</span>` : ""}
          </div>
        </div>
        <div class="score-badge ${scoreClass(job.fit_score)}">${job.fit_score || 0}</div>
      </div>
      
      ${job.fit_reason ? `<div class="reason">🤖 ${escapeHtml(job.fit_reason)}</div>` : ""}

      <div class="actions">
        <button class="primary" onclick="openOriginalUrl('${job.id}', '${escapeJs(job.application_url)}')">View & Apply →</button>
        <button class="secondary" onclick="markApplied('${job.id}')">Mark Applied</button>
        <button class="subtle" onclick="ignoreJob('${job.id}')">Not Interested</button>
      </div>
    </div>
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

function openOriginalUrl(jobId, url) {
  if (url && url !== "undefined") {
    window.open(url, "_blank");
  } else {
    alert("Application URL not available.");
  }
}

async function loadJobs() {
  jobListEl.innerHTML = `<div class="empty-state">Loading latest jobs from Supabase...</div>`;
  
  let query = sb.from("jobs").select("*").eq("status", "new").order("fit_score", { ascending: false });

  const track = trackFilter.value;
  const tier = tierFilter.value;
  const minScore = parseInt(minScoreEl.value, 10);
  const loc = locFilter.value;
  const search = searchInput.value.trim().toLowerCase();

  if (track !== "all") query = query.eq("track", track);
  if (tier !== "all") query = query.eq("difficulty_tier", tier);
  if (minScore > 0) query = query.gte("fit_score", minScore);
  if (loc === "prio1") query = query.eq("location_priority", 1);
  if (loc === "prio2") query = query.lte("location_priority", 2);

  const { data, error } = await query;
  
  if (error) {
    jobListEl.innerHTML = `<div class="empty-state">Error loading jobs: ${escapeHtml(error.message)}</div>`;
    return;
  }

  let filtered = data || [];
  if (search) {
    filtered = filtered.filter(j => 
      (j.title && j.title.toLowerCase().includes(search)) ||
      (j.company_name && j.company_name.toLowerCase().includes(search))
    );
  }

  updateStats(filtered);
  renderJobs(filtered);
}

async function markApplied(id) {
  await sb.from("jobs").update({ status: "applied", applied_at: new Date().toISOString() }).eq("id", id);
  loadJobs();
}

async function ignoreJob(id) {
  await sb.from("jobs").update({ status: "ignored" }).eq("id", id);
  loadJobs();
}

searchInput.addEventListener("input", loadJobs);
trackFilter.addEventListener("change", loadJobs);
tierFilter.addEventListener("change", loadJobs);
minScoreEl.addEventListener("change", loadJobs);
locFilter.addEventListener("change", loadJobs);
refreshBtn.addEventListener("click", loadJobs);

loadJobs();
