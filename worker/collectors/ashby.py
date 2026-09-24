import requests
from typing import List, Dict, Any, Optional
from worker.collectors.base import BaseCollector

class AshbyCollector(BaseCollector):
    source_name = "ashby"

    def fetch_jobs(self, org_slug: str, company: Optional[Dict[str, Any]] = None, timeout=15) -> List[Dict[str, Any]]:
        """
        Ashby public job-postings API — no auth needed.
        Docs: https://developers.ashbyhq.com/docs/public-job-posting-api
        """
        if not org_slug:
            return []
        url = f"https://api.ashbyhq.com/posting-api/job-board/{org_slug}"
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code != 200:
                return []
            data = r.json()
        except Exception as e:
            print(f"[AshbyCollector] Request error for {org_slug}: {e}")
            return []

        jobs = []
        for j in data.get("jobs", []):
            jobs.append({
                "external_job_id": str(j.get("id")),
                "title": j.get("title", "").strip(),
                "description": (j.get("descriptionPlain") or "").strip()[:8000],
                "location": str(j.get("location", "")).strip(),
                "employment_type": j.get("employmentType"),
                "experience_requirement": None,
                "application_url": (j.get("jobUrl") or j.get("applyUrl", "")).strip(),
                "source_url": (j.get("jobUrl") or j.get("applyUrl", "")).strip(),
                "posted_at": j.get("publishedAt"),
                "updated_at": j.get("publishedAt"),
                "source": self.source_name,
            })
        return jobs

def fetch_jobs(org_slug: str, company: Optional[Dict[str, Any]] = None, timeout=15):
    return AshbyCollector().fetch_jobs(org_slug, company=company, timeout=timeout)
