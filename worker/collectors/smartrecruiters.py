import requests
from typing import List, Dict, Any, Optional
from worker.collectors.base import BaseCollector

class SmartRecruitersCollector(BaseCollector):
    source_name = "smartrecruiters"

    def fetch_jobs(self, company_identifier: str, company: Optional[Dict[str, Any]] = None, timeout=15) -> List[Dict[str, Any]]:
        """
        SmartRecruiters public posting API — no auth needed.
        Docs: https://dev.smartrecruiters.com/official-documentation/api-recommendations/postings-api/
        """
        if not company_identifier:
            return []

        url = f"https://api.smartrecruiters.com/v1/companies/{company_identifier}/postings"
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code != 200:
                return []
            data = r.json()
        except Exception as e:
            print(f"[SmartRecruitersCollector] Error for {company_identifier}: {e}")
            return []

        jobs = []
        for item in data.get("content", []):
            loc_data = item.get("location") or {}
            loc = f"{loc_data.get('city', '')}, {loc_data.get('country', '')}".strip(", ")
            job_id = str(item.get("id"))
            app_url = f"https://jobs.smartrecruiters.com/{company_identifier}/{job_id}"
            
            jobs.append({
                "external_job_id": job_id,
                "title": item.get("name", "").strip(),
                "description": f"Ref: {item.get('refNumber', '')}. Location: {loc}",
                "location": loc,
                "employment_type": (item.get("typeOfEmployment") or {}).get("label"),
                "experience_requirement": (item.get("experienceLevel") or {}).get("label"),
                "application_url": app_url,
                "source_url": app_url,
                "posted_at": item.get("releasedDate"),
                "updated_at": item.get("releasedDate"),
                "source": self.source_name,
            })
        return jobs

def fetch_jobs(company_identifier: str, company: Optional[Dict[str, Any]] = None, timeout=15):
    return SmartRecruitersCollector().fetch_jobs(company_identifier, company=company, timeout=timeout)
