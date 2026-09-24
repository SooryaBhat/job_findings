# AGENTS.md — instructions for Antigravity (or any coding agent) on this repo

## What this project is
A personal job-discovery dashboard (no auto-apply, no notifications). See
README.md for the full architecture. Two independent halves:
- `worker/` — Python script that collects + scores jobs, run on a schedule
  by `.github/workflows/collect.yml`.
- `frontend/` — plain HTML/CSS/JS dashboard, talks to Supabase directly.

## Conventions
- Keep the worker dependency-free beyond `worker/requirements.txt` — no
  heavy frameworks, this needs to run in a GitHub Actions free-tier runner.
- Keep the frontend build-step-free (plain HTML/JS + Supabase CDN script) —
  don't introduce React/Vite/webpack unless explicitly asked.
- Never hardcode API keys or the Supabase service_role key anywhere in
  `frontend/` — only `SUPABASE_ANON_KEY` belongs there (see
  `frontend/js/config.js`).
- `.env` holds real secrets and must never be committed (already in
  `.gitignore`) — always use `.env.example` as the template when adding a
  new required variable.

## Environment / secrets this project needs
See `.env.example` for the full list with links on where to get each key.
Required: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`.
Optional: `GROQ_API_KEY`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `JOOBLE_API_KEY`.

---

## Prompts to paste into Antigravity's agent chat, in order

**1. First run — verify everything is wired up correctly**
```
I've filled in my .env file and frontend/js/config.js with my real
Supabase/Gemini credentials. Run `pip install -r worker/requirements.txt`,
then run `python -m worker.seed_companies` to import my company list, then
run `python -m worker.run_collection` once and show me the output. Fix any
errors you hit (missing packages, wrong Python version, etc.) before
re-running.
```

**2. Sanity-check the results**
```
Open the Supabase dashboard link I gave you (or just tell me what to check)
and confirm the `companies` and `jobs` tables actually got populated after
that last run. Tell me how many companies got ATS-detected successfully vs
marked "unknown", and how many jobs were scored.
```

**3. Preview the dashboard locally**
```
Serve the frontend/ folder locally (e.g. `python -m http.server` from
inside frontend/) and open it in the browser tool so I can see the
dashboard rendering real data from Supabase.
```

**4. Deploy for real**
```
Help me push this repo to GitHub, then walk me through importing it into
Vercel with the root directory set to frontend/, so I have a permanent
link to my dashboard I can open from my phone.
```

**5. Turn on the scheduled checks**
```
Walk me through adding SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
GEMINI_API_KEY (and any optional keys I have) as GitHub Actions secrets on
this repo, so the twice-a-day collect.yml workflow can run automatically.
Then trigger it once manually from the Actions tab so I can confirm it
works end-to-end without me running anything locally.
```

**6. Ongoing tweaks (use anytime later)**
```
I'm getting too few / too many jobs showing up. Open worker/filters.py and
[loosen/tighten] the keyword filters — [explain what you want changed].
```
```
Add a new company called "X" that I found on Wellfound — here's their
careers page URL: [url]. Insert it into Supabase with tier "startup", the
same way the Companies page would.
```
