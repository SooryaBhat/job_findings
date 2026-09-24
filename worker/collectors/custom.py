import requests
import re
from typing import List, Dict, Any, Optional
from worker.collectors.base import BaseCollector

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

class CustomCollector(BaseCollector):
    source_name = "custom"

    def fetch_jobs(self, careers_url: str, company: Optional[Dict[str, Any]] = None, timeout=15) -> List[Dict[str, Any]]:
        """
        Custom / Unsupported Careers Page Collector:
        Best-effort inspection of custom career pages without breaking execution.
        """
        if not careers_url:
            return []

        # Graceful fetch attempt
        try:
            r = requests.get(careers_url, headers=HEADERS, timeout=timeout, allow_redirects=True)
            if r.status_code != 200:
                return []
        except Exception as e:
            print(f"[CustomCollector] Error inspecting custom URL {careers_url}: {e}")
            return []

        # Return empty list if no automated structured endpoint is available.
        # The runner will mark status as 'manual_review' or 'unsupported' for dashboard visibility.
        return []

def fetch_jobs(careers_url: str, company: Optional[Dict[str, Any]] = None, timeout=15):
    return CustomCollector().fetch_jobs(careers_url, company=company, timeout=timeout)
