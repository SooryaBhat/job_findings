import requests
import re
from typing import List, Dict, Any, Optional
from worker.collectors.base import BaseCollector

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

class WorkdayCollector(BaseCollector):
    source_name = "workday"

    def fetch_jobs(self, identifier_or_url: str, company: Optional[Dict[str, Any]] = None, timeout=15) -> List[Dict[str, Any]]:
        """
        Workday collector:
        Attempts Workday JSON CXS API endpoints if accessible, e.g.:
        https://<tenant>.wd1.myworkdayjobs.com/wday/cxs/<tenant>/<site>/jobs
        """
        if not identifier_or_url:
            return []

        # If identifier is a full URL or tenant/site pair
        url = identifier_or_url if identifier_or_url.startswith("http") else f"https://{identifier_or_url}"
        
        # Try to extract tenant and site name from URL
        match = re.search(r"https?://([^/]+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([^/?#]+)", url)
        if not match:
            # Check if careers_url in company object provides a Workday URL
            careers_url = (company or {}).get("careers_url", "")
            match = re.search(r"https?://([^/]+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([^/?#]+)", careers_url)

        if match:
            host_tenant = match.group(1)
            site_name = match.group(2)
            api_url = f"https://{host_tenant}.myworkdayjobs.com/wday/cxs/{host_tenant}/{site_name}/jobs"
            payload = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}
            try:
                r = requests.post(api_url, json=payload, headers=HEADERS, timeout=timeout)
                if r.status_code == 200:
                    data = r.json()
                    jobs = []
                    for item in data.get("jobPostings", []):
                        external_path = item.get("externalPath", "")
                        job_url = f"https://{host_tenant}.myworkdayjobs.com/{site_name}{external_path}" if external_path else url
                        jobs.append({
                            "external_job_id": item.get("bulletFields", [{}])[0] if item.get("bulletFields") else external_path,
                            "title": item.get("title", "").strip(),
                            "description": f"Posted: {item.get('postedOn', '')}. Location: {item.get('locationsText', '')}",
                            "location": item.get("locationsText", "").strip(),
                            "employment_type": None,
                            "experience_requirement": None,
                            "application_url": job_url,
                            "source_url": job_url,
                            "posted_at": None,
                            "updated_at": None,
                            "source": self.source_name,
                        })
                    return jobs
            except Exception as e:
                print(f"[WorkdayCollector] API request failed for {url}: {e}")

        return []

def fetch_jobs(identifier_or_url: str, company: Optional[Dict[str, Any]] = None, timeout=15):
    return WorkdayCollector().fetch_jobs(identifier_or_url, company=company, timeout=timeout)
