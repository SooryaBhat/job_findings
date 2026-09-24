"""
Master Company List Importer.
Safely upserts company records into Supabase without creating duplicates.
Compatible with base Supabase schema.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from worker.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from worker.collectors import detector

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "companies_seed.csv")


def seed():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("[seed] Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return

    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        existing_rows = sb.table("companies").select("id, name, careers_url, ats, ats_identifier").execute().data
    except Exception as e:
        print(f"[seed] Failed to query companies table: {e}")
        return

    existing_map = {c["name"].strip().lower(): c for c in existing_rows}

    if not os.path.exists(CSV_PATH):
        print(f"[seed] CSV file not found at {CSV_PATH}")
        return

    added = 0
    updated = 0

    with open(CSV_PATH, encoding="utf-8-sig", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue

            tier = (row.get("tier") or "good").strip()
            careers_url = (row.get("careers_url") or "").strip() or None

            key = name.lower()
            if key in existing_map:
                existing_item = existing_map[key]
                updates = {}
                if careers_url and not existing_item.get("careers_url"):
                    updates["careers_url"] = careers_url
                    ats, ident = detector.detect(careers_url)
                    updates["ats"] = ats or "unknown"
                    updates["ats_identifier"] = ident
                
                if updates:
                    sb.table("companies").update(updates).eq("id", existing_item["id"]).execute()
                    updated += 1
                continue

            # Detect ATS if careers_url is provided
            ats, ident = "pending", None
            if careers_url:
                ats, ident = detector.detect(careers_url)

            row_data = {
                "name": name,
                "careers_url": careers_url,
                "tier": tier,
                "ats": ats or "unknown",
                "ats_identifier": ident,
                "active": True,
            }

            try:
                sb.table("companies").insert(row_data).execute()
                added += 1
            except Exception as e:
                print(f"[seed insert error] {name}: {e}")

    print(f"Company import complete. Added: {added} new, Updated: {updated} existing.")


if __name__ == "__main__":
    seed()
