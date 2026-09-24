"""
Deterministic Pre-Filters and Location Priority Evaluation.
Runs BEFORE any LLM call to save quota and filter irrelevant senior roles.
"""
import re
from typing import Tuple

TITLE_INCLUDE = [
    "ai", "ml", "machine learning", "deep learning", "data scien", "data engineer",
    "data analyst", "business analyst", "product analyst", "bi analyst", "nlp", "genai", "llm",
    "computer vision", "software engineer", "software developer", "sde", "backend",
    "full stack", "fullstack", "python developer", "developer", "engineer",
    "analyst", "graduate", "fresher", "trainee", "intern", "associate",
]

# Reject only explicit senior/leadership titles
TITLE_EXCLUDE = [
    "senior", "sr.", "sr ", "staff", "principal", "lead", "manager", "director",
    "head of", "head ", "vp ", "vice president", "architect", "chief", "president",
    "engineering manager", "technical lead", "tech lead",
]

EXPERIENCE_EXCLUDE_PATTERNS = [
    r"\b([5-9]|1[0-9])\+?\s*[-to]*\s*years?\b",    # 5+ years, 5-8 years, 10 years
    r"\bminimum\s+([5-9]|1[0-9])\s+years?\b",
    r"\bat\s+least\s+([5-9]|1[0-9])\s+years?\b",
    r"\b([5-9]|1[0-9])\+\s*yrs?\b",
]

# Location priorities
PRIORITY_1_LOCATIONS = ["bangalore", "bengaluru", "remote india", "remote (india)", "india (remote)", "remote - india"]
PRIORITY_2_LOCATIONS = ["hyderabad", "pune", "mumbai", "chennai", "gurgaon", "gurugram", "noida", "delhi", "ncr"]
PRIORITY_3_LOCATIONS = ["india", "remote", "hybrid", "ahmedabad", "kolkata", "kochi", "coimbatore", "indore"]


def title_passes(title: str) -> bool:
    if not title:
        return False
    t = title.lower()
    
    # Check senior exclusions
    for bad in TITLE_EXCLUDE:
        # Match word boundaries or distinct phrases
        if re.search(r"\b" + re.escape(bad) + r"\b", t):
            return False

    # Check target role includes
    if any(good in t for good in TITLE_INCLUDE):
        return True
    return False


def experience_ok(text: str) -> bool:
    """Reject postings that explicitly demand senior-level experience (5+ years)."""
    if not text:
        return True
    t = text.lower()
    for pattern in EXPERIENCE_EXCLUDE_PATTERNS:
        if re.search(pattern, t):
            return False
    return True


def get_location_priority(location: str) -> Tuple[int, bool]:
    """
    Returns (priority_score, passes_filter)
    Priority:
      1 = Bangalore / Remote India
      2 = Hyderabad, Pune, Mumbai, Chennai, Gurgaon, Noida / Delhi NCR
      3 = Other Indian locations / Generic Remote / India
      0 = Outside India (reject)
    """
    if not location:
        return 1, True  # Unspecified location -> allow through for LLM scoring

    loc = location.lower()

    # Check Priority 1
    if any(p1 in loc for p1 in PRIORITY_1_LOCATIONS):
        return 1, True

    # Check Priority 2
    if any(p2 in loc for p2 in PRIORITY_2_LOCATIONS):
        return 2, True

    # Check Priority 3
    if any(p3 in loc for p3 in PRIORITY_3_LOCATIONS):
        return 3, True

    # Check if explicitly outside India
    foreign_keywords = ["united states", "usa", "uk", "london", "canada", "germany", "singapore", "australia"]
    if any(fk in loc for fk in foreign_keywords) and "remote" not in loc:
        return 0, False

    # Default to Priority 3 for ambiguous locations
    return 3, True


def passes_all_filters(title: str, description: str, location: str) -> Tuple[bool, int]:
    if not title_passes(title):
        return False, 0
    if not experience_ok(f"{title} {description or ''}"):
        return False, 0
    
    loc_prio, loc_ok = get_location_priority(location)
    if not loc_ok:
        return False, 0
        
    return True, loc_prio
