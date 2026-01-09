import html
import re
from typing import Any

def clean_html(raw_html: str) -> str:
    if not isinstance(raw_html, str):
        return ""
    
    if len(raw_html) > 10000:
        raw_html = raw_html[:10000]
    
    text = html.unescape(raw_html)

    text = re.sub(r'<[^>]+>', ' ', text)
    
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text[:500] if len(text) > 500 else text


def list_to_str(value: Any) -> str:
    if isinstance(value, list):
        # Limit list size to prevent DoS
        limited_list = value[:100] if len(value) > 100 else value
        return ", ".join([str(v)[:100] for v in limited_list if v is not None])
    return str(value)[:1000] if value is not None else ""

def build_job_text(row) -> str:
    # Handle both dict and pandas Series
    if hasattr(row, 'get'):
        get_func = row.get
    else:
        get_func = lambda key, default="": getattr(row, key, default)
    
    title = str(get_func("jobTitle", ""))
    desc = clean_html(str(get_func("jobDescription", "")))
    skills = list_to_str(get_func("skills", []))
    languages = list_to_str(get_func("languages", []))
    city = str(get_func("city", ""))
    province = str(get_func("province", ""))
    country = str(get_func("country", ""))
    experience = str(get_func("experienceLevel", ""))
    special = str(get_func("specialNotes", ""))

    parts = [
        (title + " ") * 3,
        (skills + " ") * 2,
        desc,
        experience,
        languages,
        city,
        province,
        country,
        special,
    ]

    return " ".join([p for p in parts if p])

def build_candidate_text(candidate) -> str:
    if not candidate:
        candidate = {}

    # Handle both dict and pandas Series
    if hasattr(candidate, 'get'):
        get_func = candidate.get
    else:
        get_func = lambda key, default="": getattr(candidate, key, default)

    headline = str(get_func("headline", ""))
    desired_title = str(get_func("desired_title", get_func("jobTitle", "")))
    skills_raw = get_func("skills", "")
    if isinstance(skills_raw, list):
        skills = ", ".join(str(s) for s in skills_raw)
    else:
        skills = str(skills_raw)

    summary = str(get_func("summary", get_func("professionalSummary", "")))
    experience = str(get_func("experience", ""))
    city = str(get_func("city", ""))
    country = str(get_func("country", ""))

    parts = [
        (headline + " ") * 3 if headline else "",
        (desired_title + " ") * 3 if desired_title else "",
        (skills + " ") * 2 if skills else "",
        summary,
        experience,
        city,
        country,
    ]

    return " ".join([p for p in parts if p])
