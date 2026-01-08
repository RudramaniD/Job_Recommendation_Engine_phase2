import re
from typing import Dict, Any, Set

def jaccard_skill_overlap(candidate_skills_raw: Any, job_skills_raw: Any) -> float:
    def to_set(v):
        if isinstance(v, list):
            return {str(s).strip().lower() for s in v if s}
        if isinstance(v, str):
            return {s.strip().lower() for s in v.split(",") if s.strip()}
        return set()

    cand = to_set(candidate_skills_raw)
    job = to_set(job_skills_raw)

    if not cand or not job:
        return 0.0

    inter = len(cand & job)
    union = len(cand | job)
    return inter / union if union > 0 else 0.0

def normalize_text_basic(s: str) -> Set[str]:
    if not isinstance(s, str):
        return set()
    tokens = re.split(r"[^a-zA-Z0-9]+", s.lower())
    return {t for t in tokens if t}

def location_score_fn(cand_city: str, cand_province: str, cand_country: str, 
                     job_city: str, job_province: str, job_country: str) -> float:
    cand_city = (cand_city or "").strip().lower()
    cand_province = (cand_province or "").strip().lower()
    cand_country = (cand_country or "").strip().lower()

    job_city = (job_city or "").strip().lower()
    job_province = (job_province or "").strip().lower()
    job_country = (job_country or "").strip().lower()

    if cand_country and job_country and cand_country != job_country:
        return 0.0

    if cand_city and job_city and cand_city == job_city and cand_province == job_province:
        return 1.0
    if cand_city and job_city and cand_city == job_city:
        return 0.8
    if cand_province and job_province and cand_province == job_province:
        return 0.6
    if cand_country and job_country and cand_country == job_country:
        return 0.4
    return 0.0

def title_score_fn(candidate_title: str, job_title: str) -> float:
    cand_tokens = normalize_text_basic(candidate_title)
    job_tokens = normalize_text_basic(job_title)
    if not cand_tokens or not job_tokens:
        return 0.0
    inter = len(cand_tokens & job_tokens)
    union = len(cand_tokens | job_tokens)
    return inter / union if union > 0 else 0.0

def experience_score_fn(candidate_exp: str, job_exp: str) -> float:
    cand = (candidate_exp or "").strip().lower()
    job = (job_exp or "").strip().lower()
    if not cand or not job:
        return 0.0
    if cand == job:
        return 1.0
    if normalize_text_basic(cand) & normalize_text_basic(job):
        return 0.7
    return 0.4
