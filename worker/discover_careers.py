"""
Job Radar — Automatic Company Career-Source Discovery Worker.

Usage:
  python -m worker.discover_careers --sample 10   (Runs discovery on 10 sample companies)
  python -m worker.discover_careers --all         (Runs discovery on all active companies in Supabase)
"""
import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from worker.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from worker.collectors.discovery import discover_company_career_source


def get_client():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise SystemExit("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def run_discovery(limit: int = 0):
    sb = get_client()

    try:
        query = sb.table("companies").select("*").eq("active", True)
        if limit > 0:
            query = query.limit(limit)
        companies = query.execute().data
    except Exception as e:
        print(f"[Error] Failed to fetch companies from Supabase: {e}")
        return

    total = len(companies)
    print(f"Starting automatic career discovery for {total} active companies...\n")
    print(f"{'Company':<30} | {'Careers URL':<45} | {'Platform':<18} | {'Status':<15} | {'Discovery Method/Notes'}")
    print("-" * 135)

    stats = {
        "total": total,
        "discovered_urls": 0,
        "greenhouse": 0,
        "lever": 0,
        "ashby": 0,
        "workday": 0,
        "smartrecruiters": 0,
        "icims": 0,
        "successfactors": 0,
        "taleo": 0,
        "custom": 0,
        "manual_review": 0,
        "failed": 0,
        "working_collectors": 0,
    }

    for c in companies:
        name = c.get("name", "Unknown")
        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            careers_url, ats, ident, status, method_or_err = discover_company_career_source(c)
        except Exception as e:
            careers_url, ats, ident, status, method_or_err = None, "unknown", None, "manual_review", f"Discovery error: {e}"

        # Update stats
        if careers_url:
            stats["discovered_urls"] += 1

        ats_clean = (ats or "unknown").lower()
        if ats_clean in stats:
            stats[ats_clean] += 1
        else:
            stats["custom"] += 1

        if status == "working":
            stats["working_collectors"] += 1
        elif status in ("manual_review", "needs_review"):
            stats["manual_review"] += 1

        err_msg = method_or_err if status in ("manual_review", "failed") else None
        
        # Save back to Supabase companies table using base schema fields
        update_payload = {
            "ats": ats or "unknown",
            "ats_identifier": ident,
            "last_detect_attempt_at": now_iso,
        }
        if careers_url:
            update_payload["careers_url"] = careers_url

        try:
            sb.table("companies").update(update_payload).eq("id", c["id"]).execute()
        except Exception as e:
            print(f"[Error] Failed to update {name} in Supabase: {e}")

        # Display formatted row
        url_disp = (careers_url[:42] + "...") if careers_url and len(careers_url) > 45 else (careers_url or "None")
        plat_disp = f"{ats}{' (' + ident + ')' if ident else ''}"
        plat_disp = (plat_disp[:16] + "..") if len(plat_disp) > 18 else plat_disp
        status_disp = status
        err_disp = err_msg or method_or_err or ""

        print(f"{name[:28]:<30} | {url_disp:<45} | {plat_disp:<18} | {status_disp:<15} | {err_disp}")

    # Summary Report
    print("\n" + "=" * 80)
    print("CAREER DISCOVERY SUMMARY REPORT")
    print("=" * 80)
    print(f"Total Companies Processed         : {stats['total']}")
    print(f"Discovered Careers URLs           : {stats['discovered_urls']}")
    print(f"Working Collectors (Ready)        : {stats['working_collectors']}")
    print("-" * 50)
    print(f"  • Greenhouse                    : {stats['greenhouse']}")
    print(f"  • Lever                         : {stats['lever']}")
    print(f"  • Ashby                         : {stats['ashby']}")
    print(f"  • Workday                       : {stats['workday']}")
    print(f"  • SmartRecruiters               : {stats['smartrecruiters']}")
    print(f"  • iCIMS                         : {stats['icims']}")
    print(f"  • SAP SuccessFactors            : {stats['successfactors']}")
    print(f"  • Taleo                         : {stats['taleo']}")
    print(f"  • Custom Careers Pages          : {stats['custom']}")
    print(f"  • Manual Review                 : {stats['manual_review']}")
    print(f"  • Failed                        : {stats['failed']}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Career Source Discovery")
    parser.add_argument("--sample", type=int, default=0, help="Run discovery on N sample companies")
    parser.add_argument("--all", action="store_true", help="Run discovery on all active companies")
    args = parser.parse_args()

    sample_limit = args.sample if args.sample > 0 else (0 if args.all else 10)
    run_discovery(limit=sample_limit)
