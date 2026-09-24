import requests
from worker.config import JOOBLE_API_KEY


def search(keywords: str, location: str = "Bangalore", timeout=15):
    """
    Jooble API — free, request a key at https://jooble.org/api/about
    """
    if not JOOBLE_API_KEY:
        return []

    url = f"https://jooble.org/api/{JOOBLE_API_KEY}"
    payload = {"keywords": keywords, "location": location}
    r = requests.post(url, json=payload, timeout=timeout)
    if r.status_code != 200:
        return []
    data = r.json()
    jobs = []
    for j in data.get("jobs", []):
        jobs.append({
            "external_job_id": j.get("link", ""),  # jooble has no stable id, use link
            "title": j.get("title", ""),
            "description": (j.get("snippet") or "")[:8000],
            "location": j.get("location", ""),
            "application_url": j.get("link", ""),
            "company_name": j.get("company", "Unknown"),
            "posted_at": j.get("updated"),
            "source": "jooble",
        })
    return jobs
