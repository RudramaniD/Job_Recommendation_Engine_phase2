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

def calculate_years_from_work_history(work_experience: List[Dict[str, Any]]) -> int:
    if not work_experience or not isinstance(work_experience, list):
        return 0
    
    try:
        from dateutil.relativedelta import relativedelta
        total_months = 0

        for exp in work_experience:
            if not isinstance(exp, dict):
                continue

            start_date_str = exp.get('startDate')
            if not start_date_str:
                continue

            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                continue

            end_date_str = exp.get('endDate')
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    end_date = datetime.now()
            else:
                end_date = datetime.now()

            delta = relativedelta(end_date, start_date)
            months = delta.years * 12 + delta.months
            total_months += months

        return total_months // 12
    
    except Exception:
        return 0
    
def infer_desired_title(work_experience: List[Dict[str, Any]], headline: str) -> str:
    if work_experience and isinstance(work_experience, list) and len(work_experience) > 0:
        most_recent = work_experience[0]
        if isinstance(most_recent, dict):
            job_title = most_recent.get('jobTitle','')
            if job_title and isinstance(job_title, str) and job_title.strip():
                return job_title.strip()
            
    if headline and isinstance(headline, str) and headline.strip():
        return headline.strip()
    
    return ""

def extract_experience_text(work_experience: List[Dict[str, Any]]) -> str:
    if not work_experience or not isinstance(work_experience, list):
        return ""
    
    from ..core.text_processing import clean_html

    descriptions = []
    for exp in work_experience:
        if not isinstance(exp, dict):
            continue

        job_title = exp.get('jobTitle', '')
        company = exp.get('company','')
        description = exp.get('description', '')

        if description:
            description = clean_html(description)

        parts = []
        if job_title:
            parts.append(str(job_title))
        if company:
            parts.append(f"at {company}")
        if description:
            parts.append(description[:200])

        if parts:
            descriptions.append(" ".join(parts))

    combined = " ".join(descriptions)
    return combined[:1000] if len(combined) > 1000 else combined

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
    candidate_id =  str(candidate.get("candidate_id", candidate.get("_id", "unknown")))

    import re
    candidate_id = re.sub(r'[^a-zA-Z0-9_-]', '', candidate_id) or "unknown"
    validated["candidate_id"] = candidate_id

    work_experience = candidate.get("workExperience")

    if work_experience and isinstance(work_experience, list) and len(work_experience) > 0:
        validated["years_experience"] = calculate_years_from_work_history(work_experience)
        validated["experience"] = extract_experience_text(work_experience)

        headline = candidate.get("headline", "")
        validated["desired_title"] = infer_desired_title(work_experience, headline)

    else:
        if candidate.get("years_experience") is not None:
            years_exp = candidate.get("years_experience")
            if isinstance(years_exp, (int, float)):
                validated["years_experience"] = max(0, int(years_exp))
            elif isinstance(years_exp, str) and years_exp.strip().isdigit():
                validated["years_experience"] = max(0, int(years_exp.strip()))
            else:
                validated["years_experience"] = 0
                log_validation_event("normalized", candidate_id, "invalid years_exp format -> default applied")
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

        exp_value = candidate.get("experience")
        if exp_value is None or exp_value == "":
            validated["experience"] = ""
        else:
            text = str(exp_value).strip()
            validated["experience"] = text[:1000] if len(text) > 1000 else text

        desired_title = candidate.get("desired_title", candidate.get("jobTitle", candidate.get("headline", "")))

        if desired_title is None or desired_title == "":
            validated["desired_title"] = ""
        else:
            text = str(desired_title).strip()
            validated["desired_title"] = text[:1000] if len(text) > 1000 else text

    validated["skills"] = normalize_skills(candidate.get("skills"))

    for field in ["city", "province", "country"]:
        value = candidate.get(field)
        if isinstance(value, str) and value.strip():
            validated[field] = value.strip()
        else:
            validated[field] = None
            if value == "":
                log_validation_event("normalized", candidate_id, f"Empty {field} -> None")
    
    headline_value = candidate.get("headline")
    if headline_value is None or headline_value == "":
        validated["headline"] = ""
    else:
        text = str(headline_value).strip()
        validated["headline"] = text[:1000] if len(text) > 1000 else text

    summary_value = candidate.get("summary", candidate.get("professionalSummary", ""))
    if summary_value is None or summary_value == "":
        validated["summary"] = ""
    else:
        from ..core.text_processing import clean_html
        text = clean_html(str(summary_value))
        validated["summary"] = text[:1000] if len(text) > 1000 else text

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