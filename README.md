# Job Radar

A personal job-discovery dashboard. No auto-apply, no notifications — it just
checks your target companies (plus a broad discovery layer) twice a day,
scores new postings against your profile, and shows them ranked so you know
exactly what to apply to first.

## How it works

```
companies (Supabase table)
        |
        v
Greenhouse / Lever / Ashby APIs  ---\
                                      >--- keyword+experience filter --- Gemini scoring --- jobs table --- your dashboard
Adzuna / Jooble (broad discovery) --/
```

- **Company-specific search**: for every company you add, it auto-detects
  whether they use Greenhouse, Lever, or Ashby (all have free public APIs)
  and pulls their current job listings.
- **Broad discovery**: Adzuna + Jooble (free, legal aggregator APIs) search
  for your 3 tracks across all of India/Bangalore, catching companies you
  haven't manually added.
- **Not included, on purpose**: LinkedIn, Indeed, Wellfound, Unstop, Glassdoor,
  Y Combinator's "Work at a Startup". None of these offer a public API, and
  scraping them violates their terms of service (and risks getting an
  account flagged). Keep browsing those manually — when you find a company
  there, add it by name on the Companies page and the system takes over
  monitoring it automatically (if it's on Greenhouse/Lever/Ashby).
- **Filtering happens before any LLM call** — titles like "Senior Engineer"
  or "5+ years experience" are rejected by cheap keyword rules first, so you
  never burn API quota scoring irrelevant postings.
- **Scoring** uses Gemini 2.5 Flash-Lite (free tier: ~1,000 requests/day —
  plenty), with an optional Groq fallback if you add a `GROQ_API_KEY`.
- **Difficulty tiers**: every job is tagged Reach / Competitive / Achievable —
  based on the company tier you set (Dream/High Priority/Good/Startup/Backup)
  or a built-in keyword guess for companies you haven't tagged.

## One-time setup

### 1. Create a Supabase project (free)
1. Go to https://supabase.com → New Project (free tier).
2. Once created: **SQL Editor → New query** → paste the contents of
   `supabase/schema.sql` → **Run**.
3. Go to **Project Settings → API** and copy:
   - `Project URL` → this is your `SUPABASE_URL`
   - `anon public` key → this is your `SUPABASE_ANON_KEY`
   - `service_role` key → this is your `SUPABASE_SERVICE_ROLE_KEY` (keep this one secret — never put it in frontend code)

### 2. Get a free Gemini API key
Go to https://aistudio.google.com/apikey → Create API key. This is your `GEMINI_API_KEY`.

### 3. (Optional) Free discovery + fallback keys
- Groq (LLM fallback): https://console.groq.com/keys
- Adzuna (broad job discovery): https://developer.adzuna.com/
- Jooble (broad job discovery): https://jooble.org/api/about

You can skip these three and the system still works fine using just
Greenhouse/Lever/Ashby + Gemini.

### 4. Fill in your credentials
- Copy `.env.example` to `.env` and fill in the values from steps 1–3.
  This `.env` is used by the **worker** (the script that collects/scores jobs).
- Open `frontend/js/config.js` and fill in `SUPABASE_URL` and
  `SUPABASE_ANON_KEY` directly (a static frontend can't read `.env` files —
  see the comment in that file for why the anon key is safe to put there).

### 5. Install worker dependencies and seed your company list
```bash
pip install -r worker/requirements.txt
python -m worker.seed_companies      # bulk-imports your 200-company list
python -m worker.run_collection      # runs one collection pass right now
```

### 6. Deploy the frontend (free)
Easiest: push this repo to GitHub, then import it on https://vercel.com
(free tier) with the **root directory set to `frontend/`**. No build step
needed — it's plain HTML/JS.

Or just open `frontend/index.html` directly in your browser for local use.

### 7. Turn on the twice-a-day automatic checks
1. Push this repo to GitHub.
2. Go to **Settings → Secrets and variables → Actions** on your repo and add
   each value from your `.env` as a secret (same names).
3. That's it — `.github/workflows/collect.yml` runs automatically at
   ~8:30 AM and ~6:30 PM IST every day. You can also trigger it manually
   from the **Actions** tab any time ("Run workflow").

## Adding a company later
Go to the **Companies** page on your dashboard → enter the name (and
careers page URL if you have one) → Add. The ATS gets auto-detected on the
next scheduled run (within ~12 hours). If detection says "unknown", the
company probably uses Workday or a fully custom career page — you can fill
in `ats` / `ats_identifier` manually in Supabase's Table Editor if you know
it, or just leave it: Adzuna/Jooble discovery may still surface its roles.

## Files that matter if you want to tweak things
- `worker/candidate_profile.json` — your 3 resume tracks + skills. Edit this
  as your projects/skills grow.
- `worker/filters.py` — the keyword include/exclude lists. Loosen or tighten
  these if you're getting too few or too many results.
- `worker/config.py` — the REACH_KEYWORDS / COMPETITIVE_KEYWORDS lists that
  drive the difficulty tier guess for companies you haven't manually tagged.
