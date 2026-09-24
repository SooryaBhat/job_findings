"""
Job Radar — Main Collection Worker.

Pipeline:
  1. Load active target companies dynamically from Supabase database.
  2. Perform ATS auto-detection for companies with status 'pending' or missing ATS identifier.
  3. Fetch jobs using modular collectors (Greenhouse, Lever, Ashby, Workday, SmartRecruiters, Custom).
  4. Pre-filter jobs deterministically (experience, title, India location priority).
  5. Score surviving jobs with Gemini structured evaluation.
  6. Normalize & deduplicate into Supabase `jobs` table.
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from worker.config import (
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
    REACH_KEYWORDS, COMPETITIVE_KEYWORDS,
)
from worker.collectors import (
    detector, greenhouse, lever, ashby, workday, smartrecruiters, custom
)
from worker.filters import passes_all_filters
from worker.scoring import score_job

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE_PATH = os.path.join(HERE, "candidate_profile.json")

def load_profile():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH) as f:
            return json.load(f)
    return {"tracks": ["ai_ml_ds", "software", "data_analyst"]}

PROFILE = load_profile()


def get_client():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise SystemExit("Missing SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY in .env")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def dedupe_key(company_id_or_name: str, external_id: str, title: str, url: str) -> str:
    raw = f"{company_id_or_name}:{external_id}" if external_id else f"{company_id_or_name}:{title}:{url}"
    return hashlib.sha256(raw.encode()).hexdigest()


def difficulty_tier(company_name: str, company_tier: Optional[str]) -> str:
    tier_map = {
        "dream": "reach",
        "high_priority": "reach",
        "good": "competitive",
        "startup": "achievable",
        "backup": "achievable",
    }
    if company_tier and company_tier.lower() in tier_map:
        return tier_map[company_tier.lower()]

    name = (company_name or "").lower()
    if any(k in name for k in REACH_KEYWORDS):
        return "reach"
    if any(k in name for k in COMPETITIVE_KEYWORDS):
        return "competitive"
    return "achievable"


def run_detection(sb, companies: List[Dict[str, Any]]):
    """Auto-detect ATS and identifier for companies needing setup."""
    for c in companies:
        if c.get("ats") in ("pending", None, "") or not c.get("ats_identifier"):
            if not c.get("careers_url"):
                continue
            ats, ident = detector.detect(c["careers_url"])
            update_data = {
                "ats": ats or "unknown",
                "ats_identifier": ident,
                "last_detect_attempt_at": datetime.now(timezone.utc).isoformat(),
            }
            try:
                sb.table("companies").update(update_data).eq("id", c["id"]).execute()
                c.update(update_data)
                print(f"[detect] {c['name']}: {ats} / {ident}")
            except Exception as e:
                print(f"[detect] Failed to update {c['name']}: {e}")


def collect_jobs_for_company(company: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Dispatches to appropriate collector based on ATS type."""
    ats = (company.get("ats") or "").lower()
    ident = company.get("ats_identifier") or company.get("careers_url") or ""
    careers_url = company.get("careers_url") or ""

    if not ats or ats in ("pending", "unknown"):
        if careers_url:
            ats, ident = detector.detect(careers_url)

    try:
        if ats == "greenhouse" and ident:
            jobs = greenhouse.fetch_jobs(ident, company=company)
        elif ats == "lever" and ident:
            jobs = lever.fetch_jobs(ident, company=company)
        elif ats == "ashby" and ident:
            jobs = ashby.fetch_jobs(ident, company=company)
        elif ats == "workday" and (ident or careers_url):
            jobs = workday.fetch_jobs(ident or careers_url, company=company)
        elif ats == "smartrecruiters" and ident:
            jobs = smartrecruiters.fetch_jobs(ident, company=company)
        elif ats == "custom" or careers_url:
            jobs = custom.fetch_jobs(careers_url, company=company)
        else:
            return []

        for j in jobs:
            j["company_id"] = company["id"]
            j["company_name"] = company["name"]
            j["company_tier"] = company.get("tier")

        return jobs
    except Exception as e:
        print(f"[collect] {company['name']} failed: {e}")
        return []


def process_and_upsert_jobs(sb, company: Dict[str, Any], raw_jobs: List[Dict[str, Any]]) -> Tuple[int, int, int]:
    """Filters, scores, and upserts jobs into Supabase."""
    new_cnt = 0
    updated_cnt = 0

    for j in raw_jobs:
        title = j.get("title", "")
        desc = j.get("description", "")
        loc = j.get("location", "")
        app_url = j.get("application_url") or j.get("source_url") or ""

        if not app_url:
            continue

        passes, loc_prio = passes_all_filters(title, desc, loc)
        if not passes:
            continue

        company_id = j.get("company_id") or company.get("id")
        company_name = j.get("company_name") or company.get("name")
        ext_id = j.get("external_job_id", "")

        key = dedupe_key(company_id or company_name, ext_id, title, app_url)

        try:
            existing = sb.table("jobs").select("id").eq("dedupe_key", key).execute()
        except Exception:
            existing = None

        now_iso = datetime.now(timezone.utc).isoformat()

        if existing and existing.data:
            # Job exists -> update last_seen_at
            try:
                sb.table("jobs").update({
                    "last_seen_at": now_iso,
                    "title": title,
                    "location": loc,
                    "description": desc,
                }).eq("dedupe_key", key).execute()
                updated_cnt += 1
            except Exception as e:
                print(f"[upsert update error] {title}: {e}")
            continue

        # Score new job with Gemini
        eval_result = score_job(j, company_name, PROFILE, company_tier=company.get("tier"), location_priority=loc_prio)
        tier = difficulty_tier(company_name, company.get("tier"))

        job_row = {
            "company_id": company_id,
            "company_name": company_name,
            "external_job_id": ext_id,
            "title": title,
            "description": desc,
            "location": loc,
            "application_url": app_url,
            "source": j.get("source", company.get("ats") or "custom"),
            "posted_at": j.get("posted_at"),
            "track": eval_result["track"],
            "fit_score": eval_result["fit_score"],
            "fit_reason": eval_result["fit_reason"],
            "difficulty_tier": tier,
            "status": "new",
            "dedupe_key": key,
            "first_seen_at": now_iso,
            "last_seen_at": now_iso,
        }

        try:
            sb.table("jobs").insert(job_row).execute()
            new_cnt += 1
            print(f"[scored & inserted] {company_name} - {title} -> Fit: {eval_result['fit_score']} ({tier})")
        except Exception as e:
            print(f"[upsert insert error] {title}: {e}")

    return len(raw_jobs), new_cnt, updated_cnt


def main():
    sb = get_client()
    
    # Load all active target companies dynamically from Supabase database
    try:
        companies = sb.table("companies").select("*").eq("active", True).execute().data
    except Exception as e:
        print(f"[Error] Failed to fetch companies from Supabase: {e}")
        return

    print(f"Loaded {len(companies)} active companies from Supabase.")

    # Step 1: Run ATS Detection where missing
    run_detection(sb, companies)

    total_found = 0
    total_new = 0
    total_updated = 0

    # Step 2: Collect jobs per company
    for c in companies:
        raw_jobs = collect_jobs_for_company(c)
        found_cnt, new_cnt, updated_cnt = process_and_upsert_jobs(sb, c, raw_jobs)

        total_found += found_cnt
        total_new += new_cnt
        total_updated += updated_cnt

        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            sb.table("companies").update({
                "last_checked_at": now_iso,
                "jobs_found_count": found_cnt,
            }).eq("id", c["id"]).execute()
        except Exception as e:
            print(f"[Error] Updating company status for {c['name']}: {e}")

    print(f"\nCollection Pass Complete.")
    print(f"Companies checked: {len(companies)} | Raw postings seen: {total_found} | New jobs scored & added: {total_new} | Jobs updated: {total_updated}")


if __name__ == "__main__":
    main()
