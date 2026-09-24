import re
import requests
from typing import Tuple, Optional

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# Regex patterns: (ats_type, regex_for_identifier)
PATTERNS = [
    ("greenhouse", r"boards\.greenhouse\.io/([a-zA-Z0-9\-_]+)"),
    ("greenhouse", r"job-boards\.greenhouse\.io/([a-zA-Z0-9\-_]+)"),
    ("lever", r"jobs\.lever\.co/([a-zA-Z0-9\-_]+)"),
    ("ashby", r"jobs\.ashbyhq\.com/([a-zA-Z0-9\-_]+)"),
    ("workday", r"([a-zA-Z0-9\-_]+\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?[a-zA-Z0-9\-_]+)"),
    ("smartrecruiters", r"jobs\.smartrecruiters\.com/([a-zA-Z0-9\-_]+)"),
    ("icims", r"([a-zA-Z0-9\-_]+\.icims\.com)"),
    ("successfactors", r"([a-zA-Z0-9\-_]+\.successfactors\.com)"),
    ("taleo", r"([a-zA-Z0-9\-_]+\.taleo\.net)"),
]

def detect(careers_url: str, timeout=15) -> Tuple[Optional[str], Optional[str]]:
    """
    Inspects careers page URL & HTML to determine ATS platform and identifier.
    Returns: (ats_type, ats_identifier)
    """
    if not careers_url:
        return "unknown", None

    url = careers_url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    # First check URL string directly
    for ats, pattern in PATTERNS:
        m = re.search(pattern, url, re.IGNORECASE)
        if m:
            return ats, m.group(1)

    # Fetch page HTML and follow redirects
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        final_url = r.url
        html = r.text
    except Exception as e:
        print(f"[Detector] Failed to reach {url}: {e}")
        return "unknown", None

    # Check post-redirect final URL
    for ats, pattern in PATTERNS:
        m = re.search(pattern, final_url, re.IGNORECASE)
        if m:
            return ats, m.group(1)

    # Check HTML source code for embedded iframe/links
    for ats, pattern in PATTERNS:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            return ats, m.group(1)

    # Heuristic checks for Workday/SmartRecruiters HTML elements
    if "myworkdayjobs.com" in html.lower() or "workday" in html.lower():
        m_wd = re.search(r"([a-zA-Z0-9\-_]+\.myworkdayjobs\.com/[^\"'\s>]+)", html, re.IGNORECASE)
        if m_wd:
            return "workday", m_wd.group(1)
        return "workday", None

    if "smartrecruiters.com" in html.lower():
        m_sr = re.search(r"jobs\.smartrecruiters\.com/([a-zA-Z0-9\-_]+)", html, re.IGNORECASE)
        if m_sr:
            return "smartrecruiters", m_sr.group(1)
        return "smartrecruiters", None

    return "custom", None
