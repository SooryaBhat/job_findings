import json
import re
import time
import requests
from typing import Dict, Any, Optional
from worker.config import GEMINI_API_KEY

PROMPT_TEMPLATE = """You are an expert tech recruiter evaluating a job posting for a candidate.
Respond strictly with ONLY a JSON object. No markdown code blocks, no preambles.

CANDIDATE PROFILE:
{profile}

JOB POSTING:
Company: {company} (Priority Tier: {company_tier})
Title: {title}
Location: {location}
Description: {description}

Evaluate the posting against the candidate's profile.
Return a JSON object strictly matching this schema:
{{
  "track": "ai_ml_ds" | "software" | "data_analyst" | "other",
  "role_relevance": <integer 0-100>,
  "skill_match": <integer 0-100>,
  "experience_fit": <integer 0-100>,
  "location_fit": <integer 0-100>,
  "ai_ml_relevance": <integer 0-100>,
  "career_value": <integer 0-100>,
  "apply_recommendation": <boolean true/false>,
  "reason": "<short sentence under 25 words explaining the match>"
}}
"""


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        # Fallback regex search for json object
        m = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
    return None


def _call_gemini(prompt: str, timeout=30) -> Optional[Dict[str, Any]]:
    if not GEMINI_API_KEY:
        return None
    time.sleep(1)
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-3.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    )
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        r = requests.post(url, json=body, timeout=timeout)
        if r.status_code != 200:
            print(f"[Scoring] Gemini error status {r.status_code}: {r.text[:200]}")
            return None
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return _extract_json(text)
    except Exception as e:
        print(f"[Scoring] Gemini API call exception: {e}")
        return None


def calculate_weighted_score(
    eval_data: Dict[str, Any], company_tier: Optional[str] = None, location_priority: int = 1
) -> int:
    """
    Weighted Scoring Formula:
    Role relevance = 25%
    Skill match = 25%
    Experience eligibility = 15%
    Location = 10%
    Company priority = 10%
    AI/ML relevance = 10%
    Career value = 5%
    Total = 100%
    """
    tier_scores = {
        "dream": 100,
        "high_priority": 90,
        "good": 80,
        "startup": 70,
        "backup": 50,
        "unclassified": 60,
    }
    company_score = tier_scores.get((company_tier or "").lower(), 65)

    # Location score based on priority
    loc_score_map = {1: 100, 2: 85, 3: 70, 0: 20}
    loc_score = eval_data.get("location_fit", loc_score_map.get(location_priority, 70))

    role_rel = float(eval_data.get("role_relevance", 70))
    skill_m = float(eval_data.get("skill_match", 70))
    exp_fit = float(eval_data.get("experience_fit", 75))
    ai_ml_rel = float(eval_data.get("ai_ml_relevance", 60))
    career_val = float(eval_data.get("career_value", 70))

    final_score = (
        (role_rel * 0.25)
        + (skill_m * 0.25)
        + (exp_fit * 0.15)
        + (loc_score * 0.10)
        + (company_score * 0.10)
        + (ai_ml_rel * 0.10)
        + (career_val * 0.05)
    )

    return max(0, min(100, int(round(final_score))))


def score_job(job: dict, company_name: str, profile: dict, company_tier: Optional[str] = None, location_priority: int = 1) -> dict:
    """
    Evaluates a job posting and returns full scoring metrics.
    """
    profile_text = json.dumps(profile, indent=2)
    prompt = PROMPT_TEMPLATE.format(
        profile=profile_text,
        company=company_name,
        company_tier=company_tier or "unclassified",
        title=job.get("title", ""),
        location=job.get("location", ""),
        description=(job.get("description") or "")[:4000],
    )

    result = _call_gemini(prompt)

    if result is None:
        # Graceful heuristic fallback if Gemini API key missing/unavailable
        result = {
            "track": "software",
            "role_relevance": 70,
            "skill_match": 70,
            "experience_fit": 75,
            "location_fit": 80,
            "ai_ml_relevance": 50,
            "career_value": 70,
            "apply_recommendation": True,
            "reason": "Evaluated with heuristic fallback (LLM currently unavailable).",
        }

    # Ensure valid track string
    track = result.get("track", "software")
    if track not in ("ai_ml_ds", "software", "data_analyst", "other"):
        track = "software"

    overall_fit = calculate_weighted_score(result, company_tier=company_tier, location_priority=location_priority)

    return {
        "track": track,
        "fit_score": overall_fit,
        "role_relevance": int(result.get("role_relevance", 70)),
        "skill_match": int(result.get("skill_match", 70)),
        "experience_fit": int(result.get("experience_fit", 75)),
        "location_fit": int(result.get("location_fit", 80)),
        "career_value": int(result.get("career_value", 70)),
        "apply_recommendation": bool(result.get("apply_recommendation", True)),
        "fit_reason": str(result.get("reason", "Good match for entry-level tech role.")).strip(),
    }
