import html
import re
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import faiss

from geonamescache import GeonamesCache
from haversine import haversine, Unit
import pycountry


MONGO_URI = "mongodb+srv://skillorbit_qa_user:KekCGbwCRMDvN8l4@cluster0.euwijto.mongodb.net/skill_orbit_qa?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "skill_orbit_qa"
JOBS_COLLECTION = "jobs"

EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"

CACHE_DIR = Path("./vector_cache")
CACHE_DURATION_MINUTES = 2
FAISS_INDEX_FILE = CACHE_DIR / "jobs_index.faiss"
JOBS_DATA_FILE = CACHE_DIR / "jobs_data.pkl"
CACHE_METADATA_FILE = CACHE_DIR / "cache_metadata.pkl"

CACHE_DIR.mkdir(exist_ok=True)

MAX_SKILLS_COUNT = 50
MAX_TEXT_LENGTH = 1000
DEFAULT_EXPERIENCE_YEARS = 0

MODEL: SentenceTransformer | None = None

def log_validation_event(event_type: str, entity_id: str, reason: str):
    if event_type != "hard_constraint_violation":
        print(f"{entity_id} {event_type}: {reason}")

def normalize_skills(skills_raw):
    if skills_raw is None:
        return []
    
    if isinstance(skills_raw, str):
        if not skills_raw.strip():
            return []
        skills_list = [s.strip() for s in skills_raw.split(",")]
    elif isinstance(skills_raw, list):
        skills_list = skills_raw
    else:
        return []
    
    normalized = []
    seen = set()
    for skill in skills_list:
        if skill is None:
            continue
        skill_clean = str(skill).strip().lower()
        if skill_clean and skill_clean not in seen:
            normalized.append(skill_clean)
            seen.add(skill_clean)
            if len(normalized) >= MAX_SKILLS_COUNT:
                break

    return normalized

def validate_candidate_input(candidate: dict) -> dict:
    if not candidate or not isinstance(candidate, dict):
        log_validation_event("normalized", "unknown_candidate", "empty_candidate -> default_applied")
        return {
            "candidate_id": "unknown",
            "skills": [],
            "years_experience": DEFAULT_EXPERIENCE_YEARS,
            "city": None,
            "province": None,
            "country": None,
            "headline": "",
            "desired_title": "",
            "summary": "",
            "experience": ""
        }
    
    validated = {}
    candidate_id = str(candidate.get("candidate_id","unknown"))

    validated["candidate_id"] = candidate_id if candidate_id.strip() else "unknown"

    validated["skills"] = normalize_skills(candidate.get("skills"))

    # Handle years_experience field (should be numeric)
    if candidate.get("years_experience") is not None:
        years_exp = candidate.get("years_experience")
        if isinstance(years_exp, (int, float)):
            validated["years_experience"] = max(0, int(years_exp))
        elif isinstance(years_exp, str) and years_exp.strip().isdigit():
            validated["years_experience"] = max(0, int(years_exp.strip()))
        else:
            validated["years_experience"] = DEFAULT_EXPERIENCE_YEARS
            log_validation_event("normalized", candidate_id, "invalid years_experience format -> default applied")

    # Handle experience field (can be descriptive text)
    elif candidate.get("experience") is not None:
        exp_text = candidate.get("experience")
        if isinstance(exp_text, str) and exp_text.strip():
            # Valid descriptive experience - no logging needed
            validated["years_experience"] = DEFAULT_EXPERIENCE_YEARS  # Use default for numeric operations
        else:
            validated["years_experience"] = DEFAULT_EXPERIENCE_YEARS
            log_validation_event("normalized", candidate_id, "empty experience -> default applied")

    # No experience provided at all
    else:
        validated["years_experience"] = DEFAULT_EXPERIENCE_YEARS
        log_validation_event("normalized", candidate_id, "missing experience -> default applied")

    # Location fields -> converting empty strings to None
    for field in ["city","province","country"]:
        value = candidate.get(field)
        if isinstance(value, str) and value.strip():
            validated[field] = value.strip()
        else:
            validated[field] = None
            if value == "":
                log_validation_event("normalized", candidate_id, f"empty {field} -> None")

    # Text fields - ensure strings, handle None
    for field in ["headline","desired_title","summary","experience"]:
        value = candidate.get(field)
        if value is None or value == "":
            validated[field] = ""
        else:
            text = str(value).strip()
            validated[field] = text[:MAX_TEXT_LENGTH] if len(text) > MAX_TEXT_LENGTH else text

    return validated


def validate_job_record(job: dict) -> dict | None:
    if not job or not isinstance(job,dict):
        log_validation_event("rejected", "unknown_job","empty_job_record")
        return None
    
    job_id = str(job.get("jobId",""))

    if not job_id.strip():
        log_validation_event("rejected","unknown_job","missing jobId")
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

    location_fields = ["city","province", "country"]
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

# Layer 1 : Hard gates for eligibility constraints

def check_location_eligibility(job_work_arrangement, candidate_country, job_country):
    if not job_work_arrangement:
        return True, "no_location_constraint"
    
    arrangement = job_work_arrangement.lower().strip()

    if arrangement == "remote":
        return True, "remote_allowed"
    
    if arrangement in ["onsite","hybrid"]:
        if not candidate_country or not job_country:
            return True, "missing_location_data"
        
        if candidate_country.lower().strip() == job_country.lower().strip():
            return True, f"{arrangement}_same_country"
        else:
            return False, f"{arrangement}_requires_same_country"
        
    return True, "unknown_arrangement_allowed"
    
def check_skills_eligibility(candidate_skills, job_required_skills):
    if not job_required_skills:
        return True, "no_skill_requirements"
    
    if not candidate_skills:
        return False, "no_candidate_skills_but_required"
    
    try:
        cand_skills_set = {s.lower().strip() for s in candidate_skills if s}
        req_skills_set = {s.lower().strip() for s in job_required_skills if s}

        if not req_skills_set:
            return True, "empty_requirements"
        
        matches = len(cand_skills_set.intersection(req_skills_set))

        if matches > 0:
            return True, f"has_required_skills_{matches}_matches"
        else:
            return False, f"no_required_skill_overlap"
        
    except Exception:
        return True, "skills_check_error"
    
def check_employment_eligibility(job_employment_type, job_restrictions=None):
    if not job_restrictions:
        return True, "no_employment_restrictions"
    
    return True, "no_restrictions_defined"

# IMPLEMENTING THE ABOVE FUNCTIONS INTO ONE REUSABLE FUNCTION FOR COMPLETE CODEBASE

def apply_layer1_eligibility_filter(jobs_df, candidate):
    if jobs_df.empty:
        return jobs_df
    
    candidate_id = candidate.get('candidate_id', 'unknown')
    initial_count = len(jobs_df)
    eligible_jobs = []

    for job in jobs_df.itertuples(index=False):
        job_dict = job._asdict()
        job_id = job_dict.get('jobId', 'unknown')
        eligible = True
        rejection_reasons = []

        job_setting = job_dict.get('jobSetting', [])
        work_arrangement = None
        if isinstance(job_setting, list):
            if 'REMOTE' in job_setting:
                work_arrangement = 'remote'
            elif 'ONSITE' in job_setting:
                work_arrangement = 'onsite'
            elif 'HYBRID' in job_setting:
                work_arrangement = 'hybrid'

        location_eligible, location_reason = check_location_eligibility(
            work_arrangement,
            candidate.get('country'),
            job_dict.get('country')
        )
        if not location_eligible:
            eligible = False
            rejection_reasons.append(f"location:{location_reason}")

        skills_eligible, skills_reason = check_skills_eligibility(
            candidate.get('skills'),
            job_dict.get('skills')
        )
        if not skills_eligible:
            eligible = False
            rejection_reasons.append(f"skills:{skills_reason}")

        if eligible:
            eligible_jobs.append(job_dict)
        else:
            log_validation_event("hard_constraint_violation", job_id, " | ".join(rejection_reasons))

    if eligible_jobs:
        filtered_df = pd.DataFrame(eligible_jobs)
    else:
        filtered_df = jobs_df.iloc[0:0]

    final_count = len(filtered_df)
    log_validation_event("layer1_summary", candidate_id, f"enforced_constraints_{initial_count}_to_{final_count}_jobs")

    return filtered_df


def get_embedding_model() -> SentenceTransformer:
    global MODEL
    if MODEL is None:
        MODEL = SentenceTransformer(EMBEDDING_MODEL)
    return MODEL


gc = GeonamesCache()
cities_dict = gc.get_cities()

CITY_LOOKUP: dict[str, tuple[float, float]] = {}

for city_id, city_data in cities_dict.items():
    city_name = (city_data.get("name") or "").lower()
    country_code = (city_data.get("countrycode") or "").lower()
    lat = float(city_data.get("latitude"))
    lng = float(city_data.get("longitude"))
    if city_name and country_code:
        key = f"{city_name},{country_code}"
        CITY_LOOKUP[key] = (lat, lng)


def country_to_alpha2(country: str | None) -> str | None:
    if not country:
        return None
    country = country.strip()
    if len(country) == 2:
        return country.lower()
    try:
        return pycountry.countries.lookup(country).alpha_2.lower()
    except LookupError:
        return None


def get_coordinates(city: str, country: str) -> tuple[float, float] | None:
    city = (city or "").strip().lower()
    country_code = country_to_alpha2(country)
    if not city or not country_code:
        return None
    key = f"{city},{country_code}"
    return CITY_LOOKUP.get(key)


class VectorDBCache:
    def __init__(self):
        self.index = None
        self.jobs_df = None
        self.last_updated = None
        self.total_jobs_count = 0

    def is_cache_valid(self) -> bool:
        if not CACHE_METADATA_FILE.exists():
            return False
        try:
            with open(CACHE_METADATA_FILE, "rb") as f:
                metadata = pickle.load(f)
            last_updated = metadata.get("last_updated")
            if not last_updated:
                return False
            time_diff = datetime.now() - last_updated
            return time_diff < timedelta(minutes=CACHE_DURATION_MINUTES)
        except Exception:
            return False

    def check_mongodb_changes(self, client) -> bool:
        try:
            db = client[DB_NAME]
            coll = db[JOBS_COLLECTION]
            current_count = coll.count_documents({"status": "ACTIVE"})
            if CACHE_METADATA_FILE.exists():
                with open(CACHE_METADATA_FILE, "rb") as f:
                    metadata = pickle.load(f)
                    cached_count = metadata.get("total_jobs_count", 0)
                return current_count != cached_count
            return True
        except Exception:
            return True

    def load_from_disk(self) -> bool:
        try:
            if not FAISS_INDEX_FILE.exists() or not JOBS_DATA_FILE.exists():
                return False
            self.index = faiss.read_index(str(FAISS_INDEX_FILE))
            with open(JOBS_DATA_FILE, "rb") as f:
                self.jobs_df = pickle.load(f)
            with open(CACHE_METADATA_FILE, "rb") as f:
                metadata = pickle.load(f)
                self.last_updated = metadata.get("last_updated")
                self.total_jobs_count = metadata.get("total_jobs_count", 0)
            return True
        except Exception:
            return False

    def save_to_disk(self):
        faiss.write_index(self.index, str(FAISS_INDEX_FILE))
        with open(JOBS_DATA_FILE, "wb") as f:
            pickle.dump(self.jobs_df, f)
        metadata = {
            "last_updated": self.last_updated,
            "total_jobs_count": self.total_jobs_count,
        }
        with open(CACHE_METADATA_FILE, "wb") as f:
            pickle.dump(metadata, f)

    def build_from_mongodb(self, client):
        jobs_df = load_all_active_jobs(client)
        if jobs_df.empty:
            return

        model = get_embedding_model()
        jobs_df["combined_text"] = jobs_df.apply(build_job_text, axis=1)

        job_embeddings = model.encode(
            jobs_df["combined_text"].tolist(),
            batch_size=8,
            convert_to_numpy=True,
            show_progress_bar=True,
        )
        faiss.normalize_L2(job_embeddings)

        dim = job_embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(job_embeddings)

        self.index = index
        self.jobs_df = jobs_df
        self.last_updated = datetime.now()
        self.total_jobs_count = len(jobs_df)

        self.save_to_disk()

    def get_or_build(self, client):
        if self.is_cache_valid():
            if self.index is None:
                if not self.load_from_disk():
                    self.build_from_mongodb(client)
            if self.check_mongodb_changes(client):
                self.build_from_mongodb(client)
        else:
            self.build_from_mongodb(client)
        return self.index, self.jobs_df


vector_cache = VectorDBCache()


def connect_mongo():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    return client


def load_all_active_jobs(client) -> pd.DataFrame:
    db = client[DB_NAME]
    coll = db[JOBS_COLLECTION]
    docs = list(coll.find({"status": "ACTIVE"}))
    if not docs:
        return pd.DataFrame()
    
    valid_jobs = []
    for doc in docs:
        validated_job = validate_job_record(doc)
        if validated_job is not None:
            valid_jobs.append(validated_job)

    if not valid_jobs:
        return pd.DataFrame()

    jobs_df = pd.DataFrame(valid_jobs)
    if "jobId" not in jobs_df.columns:
        raise ValueError("jobId field is missing in jobs documents")
    jobs_df["jobId"] = jobs_df["jobId"].astype(str)
    if "_id" in jobs_df.columns:
        jobs_df["_id"] = jobs_df["_id"].astype(str)
    return jobs_df


def apply_filters_on_dataframe(jobs_df: pd.DataFrame, filters: dict | None = None) -> pd.DataFrame:
    if jobs_df.empty or not filters:
        return jobs_df

    filtered_df = jobs_df.copy()

    def as_int_or_none(value):
        if value in (None, "", []):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    date_days_raw = filters.get("date_posted_days")
    date_days = as_int_or_none(date_days_raw)
    if date_days is not None:
        since = datetime.utcnow() - timedelta(days=date_days)
        filtered_df = filtered_df[filtered_df["activatedAt"] >= since]

    work_setting = filters.get("work_setting") or []
    if work_setting:
        filtered_df = filtered_df[
            filtered_df["jobSetting"].apply(
                lambda x: any(ws in x for ws in work_setting) if isinstance(x, list) else False
            )
        ]

    job_type = filters.get("job_type") or []
    if job_type:
        filtered_df = filtered_df[filtered_df["positionType"].isin(job_type)]

    exp_levels = filters.get("experience_levels") or []
    if exp_levels:
        filtered_df = filtered_df[filtered_df["experienceLevel"].isin(exp_levels)]

    filtered_df = apply_distance_filter(filtered_df, filters)

    return filtered_df.reset_index(drop=True)


def apply_distance_filter(jobs_df: pd.DataFrame, filters: dict | None = None) -> pd.DataFrame:
    if jobs_df.empty or not filters:
        return jobs_df

    distance_km = filters.get("distance_km")
    if not distance_km:
        return jobs_df

    try:
        distance_km = float(distance_km)
    except (TypeError, ValueError):
        return jobs_df

    user_lat = filters.get("user_lat")
    user_lng = filters.get("user_lng")

    if user_lat is not None and user_lng is not None:
        try:
            user_coords = (float(user_lat), float(user_lng))
        except (TypeError, ValueError):
            user_coords = None
    else:
        user_coords = None

    if user_coords is None:
        user_city = filters.get("user_city", "")
        user_country = filters.get("user_country", "")
        user_coords = get_coordinates(user_city, user_country)

    if not user_coords:
        return jobs_df

    def job_coords_from_row(row) -> tuple[float, float] | None:
        lat = row.get("latitude")
        lng = row.get("longitude")
        if lat is not None and lng is not None:
            try:
                return float(lat), float(lng)
            except (TypeError, ValueError):
                pass
        job_city = row.get("city", "")
        job_country = row.get("country", "")
        return get_coordinates(job_city, job_country)

    def within_distance(row) -> bool:
        coords = job_coords_from_row(row)
        if not coords:
            return False
        d = haversine(user_coords, coords, unit=Unit.KILOMETERS)
        return d <= distance_km

    return jobs_df[jobs_df.apply(within_distance, axis=1)].reset_index(drop=True)


def clean_html(raw_html: str) -> str:
    if not isinstance(raw_html, str):
        return ""
    text = html.unescape(raw_html)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]


def list_to_str(value) -> str:
    if isinstance(value, list):
        return ", ".join([str(v) for v in value])
    return str(value) if value is not None else ""


def build_job_text(row):
    title = str(row.get("jobTitle", ""))
    desc = clean_html(str(row.get("jobDescription", "")))
    skills = list_to_str(row.get("skills", []))
    languages = list_to_str(row.get("languages", []))
    city = str(row.get("city", ""))
    province = str(row.get("province", ""))
    country = str(row.get("country", ""))
    experience = str(row.get("experienceLevel", ""))
    special = str(row.get("specialNotes", ""))

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


def build_candidate_text(candidate: dict) -> str:
    if not candidate:
        candidate = {}

    headline = str(candidate.get("headline", ""))
    desired_title = str(candidate.get("desired_title", candidate.get("jobTitle", "")))
    skills = str(candidate.get("skills", ""))
    summary = str(candidate.get("summary", candidate.get("professionalSummary", "")))
    experience = str(candidate.get("experience", ""))
    city = str(candidate.get("city", ""))
    country = str(candidate.get("country", ""))

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


def jaccard_skill_overlap(candidate_skills_raw, job_skills_raw) -> float:
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


def normalize_text_basic(s: str) -> set:
    if not isinstance(s, str):
        return set()
    tokens = re.split(r"[^a-zA-Z0-9]+", s.lower())
    return {t for t in tokens if t}


def location_score_fn(cand_city, cand_province, cand_country, job_city, job_province, job_country) -> float:
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


# Layer 1: Hard gates for eligibility constraints

def check_location_eligibility(job_work_arrangement, candidate_country, job_country):
    if not job_work_arrangement:
        return True, "no_location_constraint"
    
    arrangement = job_work_arrangement.lower().strip()

    if arrangement == "remote":
        return True, "remote_allowed"
    
    if arrangement in ["onsite","hybrid"]:
        if not candidate_country or not job_country:
            return True, "missing_location_data"
        
        if candidate_country.lower().strip() == job_country.lower().strip():
            return True, f"{arrangement}_same_country"
        else:
            return False, f"{arrangement}_requires_same_country"
        
    return True, "unknown_arrangement_allowed"
    
def check_skills_eligibility(candidate_skills, job_required_skills):
    if not job_required_skills:
        return True, "no_skill_requirements"
    
    if not candidate_skills:
        return False, "no_candidate_skills_but_required"
    
    try:
        cand_skills_set = {s.lower().strip() for s in candidate_skills if s}
        req_skills_set = {s.lower().strip() for s in job_required_skills if s}

        if not req_skills_set:
            return True, "empty_requirements"
        
        matches = len(cand_skills_set.intersection(req_skills_set))

        if matches > 0:
            return True, f"has_required_skills_{matches}_matches"
        else:
            return False, f"no_required_skill_overlap"
        
    except Exception:
        return True, "skills_check_error"
    
def check_employment_eligibility(job_employment_type, job_restrictions=None):
    if not job_restrictions:
        return True, "no_employment_restrictions"
    
    return True, "no_restrictions_defined"

def apply_layer1_eligibility_filter(jobs_df, candidate):
    if jobs_df.empty:
        return jobs_df
    
    candidate_id = candidate.get('candidate_id', 'unknown')
    initial_count = len(jobs_df)
    eligible_jobs = []

    for job in jobs_df.itertuples(index=False):
        job_dict = job._asdict()
        job_id = job_dict.get('jobId', 'unknown')
        eligible = True
        rejection_reasons = []

        job_setting = job_dict.get('jobSetting', [])
        work_arrangement = None
        if isinstance(job_setting, list):
            if 'REMOTE' in job_setting:
                work_arrangement = 'remote'
            elif 'ONSITE' in job_setting:
                work_arrangement = 'onsite'
            elif 'HYBRID' in job_setting:
                work_arrangement = 'hybrid'

        location_eligible, location_reason = check_location_eligibility(
            work_arrangement,
            candidate.get('country'),
            job_dict.get('country')
        )
        if not location_eligible:
            eligible = False
            rejection_reasons.append(f"location:{location_reason}")

        skills_eligible, skills_reason = check_skills_eligibility(
            candidate.get('skills'),
            job_dict.get('skills')
        )
        if not skills_eligible:
            eligible = False
            rejection_reasons.append(f"skills:{skills_reason}")

        if eligible:
            eligible_jobs.append(job_dict)
        else:
            log_validation_event("hard_constraint_violation", job_id, " | ".join(rejection_reasons))

    if eligible_jobs:
        filtered_df = pd.DataFrame(eligible_jobs)
    else:
        filtered_df = jobs_df.iloc[0:0]

    final_count = len(filtered_df)
    log_validation_event("layer1_summary", candidate_id, f"enforced_constraints_{initial_count}_to_{final_count}_jobs")

    return filtered_df


def match_jobs_for_candidate(candidate: dict, filters: dict | None = None) -> dict:

    validated_candidate = validate_candidate_input(candidate)
    client = connect_mongo()
    index, jobs_df = vector_cache.get_or_build(client)

    if jobs_df.empty:
        return {"total_matches": 0, "matches": []}

    filtered_jobs_df = apply_filters_on_dataframe(jobs_df, filters)

    if filtered_jobs_df.empty:
        return {"total_matches": 0, "matches": []}
    
    eligible_jobs_df = apply_layer1_eligibility_filter(filtered_jobs_df, validated_candidate)

    if eligible_jobs_df.empty:
        return {"total_matches":0, "matches": []}
    
    model = get_embedding_model()
    candidate_text = build_candidate_text(validated_candidate)
    cand_emb = model.encode([candidate_text], convert_to_numpy=True, show_progress_bar=False)
    faiss.normalize_L2(cand_emb)

    filtered_indices = filtered_jobs_df.index.tolist()
    sim_scores, sim_indices = index.search(cand_emb, index.ntotal)
    sim_scores = sim_scores[0]
    sim_indices = sim_indices[0]

    filtered_results = [
        (score, idx)
        for score, idx in zip(sim_scores, sim_indices)
        if idx in filtered_indices
    ]

    candidate_skills = validated_candidate.get("skills", "")
    matches = []

    for score, job_idx in filtered_results:
        if job_idx < 0:
            continue

        job_row = jobs_df.iloc[job_idx]

        loc_score = location_score_fn(
            validated_candidate.get("city"),
            validated_candidate.get("province"),
            validated_candidate.get("country"),
            job_row.get("city"),
            job_row.get("province"),
            job_row.get("country"),
        )

        title_score = title_score_fn(
            validated_candidate.get("desired_title", validated_candidate.get("jobTitle", validated_candidate.get("headline", ""))),
            job_row.get("jobTitle", ""),
        )

        exp_score = experience_score_fn(
            validated_candidate.get("experience", ""),
            job_row.get("experienceLevel", ""),
        )

        skill_score = jaccard_skill_overlap(candidate_skills, job_row.get("skills", []))
        semantic_score = float(score)

        final_score = (
            0.4 * loc_score
            + 0.3 * title_score
            + 0.2 * exp_score
            + 0.1 * skill_score
            + 0.05 * semantic_score
        )

        matches.append(
            {
                "jobId": job_row.get("jobId"),
                "jobTitle": job_row.get("jobTitle", ""),
                "city": job_row.get("city", ""),
                "province": job_row.get("province", ""),
                "country": job_row.get("country", ""),
                "locationScore": round(loc_score, 4),
                "titleScore": round(title_score, 4),
                "experienceScore": round(exp_score, 4),
                "skillScore": round(skill_score, 4),
                "semanticScore": round(semantic_score, 4),
                "finalScore": round(final_score, 4),
            }
        )

    matches = sorted(matches, key=lambda x: x["finalScore"], reverse=True)

    return {"total_matches": len(matches), "matches": matches}


if __name__ == "__main__":
    example_candidate = {
        "candidate_id": "1",
        "headline": "Customer Experience Manager | Customer Success Manager",
        "desired_title": "Training Specialist",
        "skills": "Customer Success,Client Management, Communication",
        "summary": "Customer Success / Customer Experience professional focused on building strong relationships with enterprise clients and driving adoption of AI-powered SaaS products.",
        "experience": "3+ years in customer success and account management in SaaS and B2B environments, working closely with sales and product teams to track usage metrics and improve client outcomes.",
        "location": "Ottawa, Ontario",
        "city": "Ottawa",
        "province": "Ontario",
        "country": "Canada",
    }

    example_filters = {
        "date_posted_days": None,
        "work_setting": ["HYBRID", "REMOTE"],
        "job_type": ["FULLTIME"],
        "experience_levels": [],
        "distance_km": None,
    }

    result = match_jobs_for_candidate(example_candidate, example_filters)

    print("\n" + "=" * 80)
    print(f"TOTAL MATCHES: {result['total_matches']}")
    print("=" * 80)

    print("\nTop 10 Results:")
    for i, m in enumerate(result["matches"][:10], 1):
        print(f"\n{i}. Job ID: {m['jobId']}")
        print(f"   Title: {m['jobTitle']}")
        print(f"   Location: {m['city']}, {m['province']}, {m['country']}")
        print(f"   Final Score: {m['finalScore']}")
        print(
            f"   → Location: {m['locationScore']}, "
            f"Title: {m['titleScore']}, "
            f"Exp: {m['experienceScore']}, "
            f"Skills: {m['skillScore']}, "
            f"Semantic: {m['semanticScore']}"
        )

