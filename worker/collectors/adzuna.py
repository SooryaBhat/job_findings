import requests
from worker.config import ADZUNA_APP_ID, ADZUNA_APP_KEY


def search(what: str, where: str = "Bangalore", results_per_page: int = 30, timeout=15):
    """
    Adzuna Jobs API — free developer tier, legal aggregator covering many
    Indian job boards. Docs: https://developer.adzuna.com/
    Register free at https://developer.adzuna.com/ to get APP_ID/APP_KEY.
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        return []

    url = f"https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": what,
        "where": where,
        "results_per_page": results_per_page,
        "content-type": "application/json",
    }
    r = requests.get(url, params=params, timeout=timeout)
    if r.status_code != 200:
        return []
    data = r.json()
    jobs = []
    for j in data.get("results", []):
        jobs.append({
            "external_job_id": str(j.get("id")),
            "title": j.get("title", ""),
            "description": (j.get("description") or "")[:8000],
            "location": (j.get("location") or {}).get("display_name", ""),
            "application_url": j.get("redirect_url", ""),
            "company_name": (j.get("company") or {}).get("display_name", "Unknown"),
            "posted_at": j.get("created"),
            "source": "adzuna",
        })
    return jobs
