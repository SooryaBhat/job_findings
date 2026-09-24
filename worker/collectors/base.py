"""
Base Collector Interface for Job Radar.
All ATS/careers page collectors inherit from BaseCollector.
"""
from typing import List, Dict, Any, Optional

class BaseCollector:
    source_name: str = "base"

    def fetch_jobs(self, identifier_or_url: str, company: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch and return a list of normalized job dictionaries:
        {
            "external_job_id": str,
            "title": str,
            "description": str,
            "location": str,
            "employment_type": str,
            "experience_requirement": str,
            "application_url": str,
            "source_url": str,
            "posted_at": str (ISO string or None),
            "updated_at": str (ISO string or None),
            "source": str,
        }
        """
        raise NotImplementedError("Subclasses must implement fetch_jobs")
