from typing import Dict, List, Any, Tuple
import pandas as pd
from .layer0_validation import log_validation_event

def check_location_eligibility(job_work_arrangement: str, candidate_country: str, job_country: str) -> Tuple[bool, str]:
    if not job_work_arrangement:
        return True, "no_location_constraint"
    
    arrangement = job_work_arrangement.lower().strip()

    if arrangement == "remote":
        return True, "remote_allowed"
    
    if arrangement in ["onsite", "hybrid"]:
        if not candidate_country or not job_country:
            return True, "missing_location_data"
        
        if candidate_country.lower().strip() == job_country.lower().strip():
            return True, f"{arrangement}_same_country"
        else:
            return False, f"{arrangement}_requires_same_country"
        
    return True, "unknown_arrangement_allowed"

def check_skills_eligibility(candidate_skills: List[str], job_required_skills: List[str]) -> Tuple[bool, str]:
    if not job_required_skills:
        return True, "no_skill_requirements"
    
    if not candidate_skills:
        return True, "no_candidate_skills_pass_to_scoring"
    
    try:
        cand_skills_set = {s.lower().strip() for s in candidate_skills if s}
        req_skills_set = {s.lower().strip() for s in job_required_skills if s}

        if not req_skills_set:
            return True, "empty_requirements"
        
        matches = len(cand_skills_set.intersection(req_skills_set))

        if matches > 0:
            return True, f"has_required_skills_{matches}_matches"
        else:
            return True, f"no_skill_overlap_pass_to_scoring"
        
    except Exception:
        return True, "skills_check_error"

def check_employment_eligibility(job_employment_type: str, job_restrictions: List[str] = None) -> Tuple[bool, str]:
    if not job_restrictions:
        return True, "no_employment_restrictions"
    
    return True, "no_restrictions_defined"

def apply_layer1_eligibility_filter(jobs_df: pd.DataFrame, candidate: Dict[str, Any]) -> pd.DataFrame:
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
        
        semantic_score = float(job_dict.get('semantic_score', 0.0))
        if semantic_score < 0.55:
            eligible = False
            rejection_reasons.append(f"semantic:below_threshold_{semantic_score:.3f}")

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
