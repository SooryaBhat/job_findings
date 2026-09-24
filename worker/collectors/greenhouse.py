import requests
from typing import List, Dict, Any, Optional
from worker.collectors.base import BaseCollector

class GreenhouseCollector(BaseCollector):
    source_name = "greenhouse"

    def fetch_jobs(self, board_token: str, company: Optional[Dict[str, Any]] = None, timeout=15) -> List[Dict[str, Any]]:
        """
        Greenhouse public job board API — no auth needed.
        Docs: https://developers.greenhouse.io/job-board.html
        """
        if not board_token:
            return []
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code != 200:
                return []
            data = r.json()
        except Exception as e:
            print(f"[GreenhouseCollector] Request error for {board_token}: {e}")
            return []

        jobs = []
        for j in data.get("jobs", []):
            jobs.append({
                "external_job_id": str(j.get("id")),
                "title": j.get("title", "").strip(),
                "description": (j.get("content") or "").strip()[:8000],
                "location": (j.get("location") or {}).get("name", "").strip(),
                "employment_type": None,
                "experience_requirement": None,
                "application_url": j.get("absolute_url", "").strip(),
                "source_url": j.get("absolute_url", "").strip(),
                "posted_at": j.get("updated_at"),
                "updated_at": j.get("updated_at"),
                "source": self.source_name,
            })
        return jobs

def fetch_jobs(board_token: str, company: Optional[Dict[str, Any]] = None, timeout=15):
    return GreenhouseCollector().fetch_jobs(board_token, company=company, timeout=timeout)
