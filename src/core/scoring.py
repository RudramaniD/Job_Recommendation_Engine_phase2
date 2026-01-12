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

    if cand_city and job_city and cand_city == job_city:
        return 1.0
    
    if cand_province and job_province and cand_province == job_province:
        return 0.8
    
    if cand_country and job_country and cand_country == job_country:
        return 0.5
    
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


ROLE_FAMILIES = {
    "devops": ["devops", "sre", "site reliability", "platform engineer", "infrastructure", "cloud engineer", 
               "reliability engineer", "systems engineer", "automation engineer"],
    "frontend": ["frontend", "front-end", "ui developer", "react developer", "vue developer", "angular developer"],
    "backend": ["backend", "back-end", "api developer", "server", "microservices"],
    "fullstack": ["fullstack", "full-stack", "full stack"],
    "data": ["data scientist", "data engineer", "data analyst", "machine learning", "ml engineer", "ai engineer"],
    "mobile": ["mobile developer", "ios developer", "android developer", "react native", "flutter"],
    "qa": ["qa engineer", "test engineer", "quality assurance", "automation tester", "sdet"],
    "security": ["security engineer", "cybersecurity", "infosec", "penetration tester"],
    "product": ["product manager", "product owner", "business analyst"],
    "design": ["designer", "ux designer", "ui designer", "graphic designer"],
    "management": ["engineering manager", "tech lead", "director", "vp engineering"],
}

NON_TECH_ROLES = ["facilities", "event coordinator", "business manager", "hr", "recruiter", "sales", 
                  "marketing", "finance", "accounting", "legal", "operations manager"]

def detect_role_family(title: str) -> str:
    if not title:
        return "unknown"
    
    title_lower = title.lower().strip()
    
    for non_tech in NON_TECH_ROLES:
        if non_tech in title_lower:
            return "non_tech"
    
    for family, keywords in ROLE_FAMILIES.items():
        for keyword in keywords:
            if keyword in title_lower:
                return family
    
    return "unknown"

def check_role_affinity(candidate_title: str, job_title: str) -> float:
    cand_family = detect_role_family(candidate_title)
    job_family = detect_role_family(job_title)
    
    if job_family == "non_tech":
        return 0.0
    
    if cand_family == "unknown" or job_family == "unknown":
        return 0.5
    
    if cand_family == job_family:
        return 1.0
    
    adjacent_families = {
        "devops": ["backend", "fullstack", "infrastructure"],
        "backend": ["devops", "fullstack"],
        "frontend": ["fullstack"],
        "fullstack": ["frontend", "backend", "devops"],
    }
    
    if cand_family in adjacent_families and job_family in adjacent_families.get(cand_family, []):
        return 0.7
    
    return 0.3
