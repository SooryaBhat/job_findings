import requests
from typing import List, Dict, Any, Optional
from worker.collectors.base import BaseCollector

class LeverCollector(BaseCollector):
    source_name = "lever"

    def fetch_jobs(self, site_token: str, company: Optional[Dict[str, Any]] = None, timeout=15) -> List[Dict[str, Any]]:
        """
        Lever public postings API — no auth needed.
        Docs: https://github.com/lever/postings-api
        """
        if not site_token:
            return []
        url = f"https://api.lever.co/v0/postings/{site_token}?mode=json"
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code != 200:
                return []
            data = r.json()
        except Exception as e:
            print(f"[LeverCollector] Request error for {site_token}: {e}")
            return []

        jobs = []
        for j in data:
            loc = ""
            cats = j.get("categories") or {}
            if cats.get("location"):
                loc = cats["location"]
            emp_type = cats.get("commitment", "")
            
            jobs.append({
                "external_job_id": str(j.get("id")),
                "title": j.get("text", "").strip(),
                "description": (j.get("descriptionPlain") or j.get("description") or "").strip()[:8000],
                "location": loc.strip(),
                "employment_type": emp_type.strip() if emp_type else None,
                "experience_requirement": None,
                "application_url": (j.get("applyUrl") or j.get("hostedUrl", "")).strip(),
                "source_url": (j.get("hostedUrl") or j.get("applyUrl", "")).strip(),
                "posted_at": None,
                "updated_at": None,
                "source": self.source_name,
            })
        return jobs

def fetch_jobs(site_token: str, company: Optional[Dict[str, Any]] = None, timeout=15):
    return LeverCollector().fetch_jobs(site_token, company=company, timeout=timeout)
