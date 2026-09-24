"""
Automatic Career Page & ATS Discovery Module for Job Radar.

Discovery Strategy:
  1. Direct Public ATS API Slug Probing (Greenhouse, Lever, Ashby, SmartRecruiters)
     Generates normalized company slugs and verifies active postings exist.
  2. Common Careers URL Probing
     Probes known/primary website domains with short 3s timeouts.
  3. Web Search Fallback (DuckDuckGo HTML)
     Searches for official company careers links if direct probing doesn't find an ATS.
  4. ATS Detection via Page Inspection
     Inspects discovered URLs for Greenhouse, Lever, Ashby, Workday, SmartRecruiters, iCIMS, SuccessFactors, Taleo.
"""
import re
import requests
from typing import Tuple, Optional, Dict, Any
from worker.collectors import detector

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


def generate_slugs(company_name: str) -> list[str]:
    """Generates candidate URL/board slugs for a company name."""
    name = company_name.lower().strip()
    
    # Strip common corporate suffixes
    name_clean = re.sub(r"\b(inc|llc|ltd|limited|corp|corporation|technologies|tech|solutions|services|group|labs|ai|io|india|private|pvt|advisory|consulting)\b", "", name, flags=re.IGNORECASE).strip()
    
    slug_simple = re.sub(r"[^a-z0-9]", "", name)
    slug_hyphen = re.sub(r"[^a-z0-9]+", "-", name).strip("-")
    slug_clean_simple = re.sub(r"[^a-z0-9]", "", name_clean)
    slug_clean_hyphen = re.sub(r"[^a-z0-9]+", "-", name_clean).strip("-")

    slugs = []
    for s in [slug_clean_hyphen, slug_clean_simple, slug_hyphen, slug_simple]:
        if s and s not in slugs and len(s) >= 2:
            slugs.append(s)

    return slugs


def probe_public_ats_endpoints(company_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Directly checks Greenhouse, Lever, Ashby, and SmartRecruiters public API endpoints
    using company slugs. Only matches if active postings exist.
    Returns: (ats_type, ats_identifier, careers_url)
    """
    slugs = generate_slugs(company_name)

    for slug in slugs:
        # 1. Greenhouse check
        try:
            gh_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
            r = requests.get(gh_url, timeout=3)
            if r.status_code == 200:
                data = r.json()
                if data.get("jobs") and len(data["jobs"]) > 0:
                    careers_url = f"https://boards.greenhouse.io/{slug}"
                    return "greenhouse", slug, careers_url
        except Exception:
            pass

        # 2. Lever check
        try:
            lever_url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
            r = requests.get(lever_url, timeout=3)
            if r.status_code == 200 and isinstance(r.json(), list) and len(r.json()) > 0:
                careers_url = f"https://jobs.lever.co/{slug}"
                return "lever", slug, careers_url
        except Exception:
            pass

        # 3. Ashby check
        try:
            ashby_url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
            r = requests.get(ashby_url, timeout=3)
            if r.status_code == 200:
                data = r.json()
                if data.get("jobs") and len(data["jobs"]) > 0:
                    careers_url = f"https://jobs.ashbyhq.com/{slug}"
                    return "ashby", slug, careers_url
        except Exception:
            pass

        # 4. SmartRecruiters check
        try:
            sr_url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
            r = requests.get(sr_url, timeout=3)
            if r.status_code == 200:
                data = r.json()
                if data.get("content") and len(data["content"]) > 0:
                    careers_url = f"https://jobs.smartrecruiters.com/{slug}"
                    return "smartrecruiters", slug, careers_url
        except Exception:
            pass

    return None, None, None


def probe_common_careers_urls(company_name: str, website_url: Optional[str] = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Probes standard career URL paths for a company domain with short timeouts.
    Returns (ats_type, ats_identifier, careers_url)
    """
    domains = []
    if website_url:
        w = website_url.strip()
        m = re.search(r"https?://([^/]+)", w if w.startswith("http") else f"https://{w}")
        if m:
            domains.append(m.group(1).replace("www.", ""))

    slugs = generate_slugs(company_name)
    if slugs:
        primary_slug = slugs[0]
        for ext in [".com", ".ai", ".io"]:
            dom = f"{primary_slug}{ext}"
            if dom not in domains:
                domains.append(dom)

    paths = ["/careers", "/jobs"]
    
    for dom in domains[:2]:
        for p in paths:
            target_url = f"https://{dom}{p}"
            ats, ident = detector.detect(target_url, timeout=3)
            if ats and ats != "unknown":
                return ats, ident, target_url

    return None, None, None


def search_duckduckgo_careers(company_name: str) -> Optional[str]:
    """
    Searches DuckDuckGo HTML for official careers link for company_name.
    """
    query = f"{company_name} official careers jobs"
    url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            links = re.findall(r'href="([^"]+)"', r.text)
            for link in links:
                m = re.search(r"uddg=([^&]+)", link)
                if m:
                    actual_url = requests.utils.unquote(m.group(1))
                    if "duckduckgo.com" not in actual_url and any(k in actual_url.lower() for k in ["career", "job", "greenhouse", "lever", "ashby", "workday", "smartrecruiters", "icims"]):
                        return actual_url
    except Exception as e:
        print(f"[Discovery Search] Query failed for {company_name}: {e}")

    return None


def discover_company_career_source(company: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], str, Optional[str]]:
    """
    Full career source discovery pipeline for a company object.
    Returns: (careers_url, ats_platform, ats_identifier, collector_status, discovery_method_or_error)
    """
    name = company.get("name", "").strip()
    existing_url = (company.get("careers_url") or "").strip()
    website_url = (company.get("website") or "").strip()

    # 1. Inspect existing_url first if available
    if existing_url:
        ats, ident = detector.detect(existing_url, timeout=5)
        if ats and ats != "unknown":
            status = "working" if ats in ("greenhouse", "lever", "ashby", "workday", "smartrecruiters") else "needs_review"
            return existing_url, ats, ident, status, "existing_url_detection"
        elif ats == "custom":
            return existing_url, "custom", None, "needs_review", "existing_custom_url"

    # 2. Direct Public ATS API Slug Probing (verified with active job count > 0)
    ats, ident, found_url = probe_public_ats_endpoints(name)
    if ats and found_url:
        return found_url, ats, ident, "working", "ats_slug_probing"

    # 3. Domain & Career Path Probing
    ats, ident, found_url = probe_common_careers_urls(name, website_url=website_url)
    if ats and found_url:
        status = "working" if ats in ("greenhouse", "lever", "ashby", "workday", "smartrecruiters") else "needs_review"
        return found_url, ats, ident, status, "domain_path_probing"

    # 4. Search Query Fallback
    search_url = search_duckduckgo_careers(name)
    if search_url:
        ats, ident = detector.detect(search_url, timeout=5)
        status = "working" if ats in ("greenhouse", "lever", "ashby", "workday", "smartrecruiters") else "needs_review"
        return search_url, ats or "custom", ident, status, "web_search_fallback"

    # 5. Fallback: If existing_url was provided, keep it as custom/needs_review
    if existing_url:
        return existing_url, "custom", None, "needs_review", "unsupported_custom_page"

    return None, "unknown", None, "manual_review", "Could not automatically discover official careers page"
