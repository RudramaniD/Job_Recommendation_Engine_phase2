from typing import Dict, List, Optional, Any
from datetime import datetime

def log_validation_event(event_type: str, entity_id: str, reason: str):
    # Silent logging - no console output for production
    pass

def normalize_skills(skills_raw: Any) -> List[str]:
    if skills_raw is None:
        return []
    
    if isinstance(skills_raw, str):
        if not skills_raw.strip():
            return []
        # Limit string length to prevent DoS
        if len(skills_raw) > 10000:
            skills_raw = skills_raw[:10000]
        skills_list = [s.strip() for s in skills_raw.split(",")]
    elif isinstance(skills_raw, list):
        # Limit list size to prevent DoS
        skills_list = skills_raw[:100]
    else:
        return []
    
    normalized = []
    seen = set()
    for skill in skills_list:
        if skill is None:
            continue
        skill_clean = str(skill).strip().lower()
        # Sanitize skill names
        import re
        skill_clean = re.sub(r'[^a-zA-Z0-9\s+#.-]', '', skill_clean)
        if skill_clean and skill_clean not in seen and len(skill_clean) <= 100:
            normalized.append(skill_clean)
            seen.add(skill_clean)
            if len(normalized) >= 50: 
                break

    return normalized

def validate_candidate_input(candidate: Dict[str, Any]) -> Dict[str, Any]:
    if not candidate or not isinstance(candidate, dict):
        log_validation_event("normalized", "unknown_candidate", "empty_candidate -> default_applied")
        return {
            "candidate_id": "unknown",
            "skills": [],
            "years_experience": 0,
            "city": None,
            "province": None,
            "country": None,
            "headline": "",
            "desired_title": "",
            "summary": "",
            "experience": ""
        }
    
    validated = {}
    candidate_id = str(candidate.get("candidate_id", "unknown"))
    
    # Sanitize candidate_id to prevent injection
    import re
    candidate_id = re.sub(r'[^a-zA-Z0-9_-]', '', candidate_id) or "unknown"
    validated["candidate_id"] = candidate_id
    validated["skills"] = normalize_skills(candidate.get("skills"))

    # Handle years_experience field
    if candidate.get("years_experience") is not None:
        years_exp = candidate.get("years_experience")
        if isinstance(years_exp, (int, float)):
            validated["years_experience"] = max(0, int(years_exp))
        elif isinstance(years_exp, str) and years_exp.strip().isdigit():
            validated["years_experience"] = max(0, int(years_exp.strip()))
        else:
            validated["years_experience"] = 0
            log_validation_event("normalized", candidate_id, "invalid years_experience format -> default applied")
    elif candidate.get("experience") is not None:
        exp_text = candidate.get("experience")
        if isinstance(exp_text, str) and exp_text.strip():
            validated["years_experience"] = 0
        else:
            validated["years_experience"] = 0
            log_validation_event("normalized", candidate_id, "empty experience -> default applied")
    else:
        validated["years_experience"] = 0
        log_validation_event("normalized", candidate_id, "missing experience -> default applied")

    # Location fields
    for field in ["city", "province", "country"]:
        value = candidate.get(field)
        if isinstance(value, str) and value.strip():
            validated[field] = value.strip()
        else:
            validated[field] = None
            if value == "":
                log_validation_event("normalized", candidate_id, f"empty {field} -> None")

    # Text fields
    for field in ["headline", "desired_title", "summary", "experience"]:
        value = candidate.get(field)
        if value is None or value == "":
            validated[field] = ""
        else:
            text = str(value).strip()
            validated[field] = text[:1000] if len(text) > 1000 else text

    return validated

def validate_job_record(job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not job or not isinstance(job, dict):
        log_validation_event("rejected", "unknown_job", "empty_job_record")
        return None
    
    job_id = str(job.get("jobId", ""))
    if not job_id.strip():
        log_validation_event("rejected", "unknown_job", "missing jobId")
        return None
    
    status = job.get("status", "")
    if status != "ACTIVE":
        log_validation_event("rejected", job_id, f"status={status} (NOT ACTIVE)")
        return None
    
    job_title = job.get("jobTitle", "")
    if not job_title or not str(job_title).strip():
        log_validation_event("rejected", job_id, "missing job_title")
        return None
    
    validated = job.copy()
    validated["skills"] = normalize_skills(job.get("skills", []))

    location_fields = ["city", "province", "country"]
    has_location = any(job.get(field) for field in location_fields)

    if not has_location:
        job_setting = job.get("jobSetting", [])
        if isinstance(job_setting, list) and "REMOTE" in job_setting:
            validated["location_type"] = "remote"
        else:
            validated["location_type"] = "unresolved"
            log_validation_event("normalized", job_id, "missing location → marked unresolved")
    
    # Date field validation
    try:
        activated_at = job.get("activatedAt")
        if activated_at and not isinstance(activated_at, datetime):
            if isinstance(activated_at, str):
                validated["activatedAt"] = datetime.fromisoformat(activated_at.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        log_validation_event("normalized", job_id, "invalid activatedAt → kept original")
    
    return validated