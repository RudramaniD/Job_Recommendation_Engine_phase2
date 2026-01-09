from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class WorkExperience(BaseModel):
    jobTitle: str
    company: str
    workType: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    startDate: str
    endDate: Optional[str] = None
    description: Optional[str] = None


class JobPreferences(BaseModel):
    workSetting: Optional[List[str]] = None
    workType: Optional[str] = None
    minBasePay: Optional[Dict[str, Any]] = None
    willingToRelocate: Optional[bool] = None


class CandidatePayload(BaseModel):
    _id: Optional[str] = None
    candidate_id: Optional[str] = None
    fullName: Optional[str] = None
    email: Optional[str] = None
    headline: Optional[str] = None
    professionalSummary: Optional[str] = None
    skills: Optional[List[str]] = []
    languages: Optional[List[str]] = []
    workExperience: Optional[List[WorkExperience]] = []
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    jobPreferences: Optional[JobPreferences] = None


class FiltersRequest(BaseModel):
    work_setting: Optional[List[str]] = Field(None, max_items=10)
    job_type: Optional[List[str]] = Field(None, max_items=10)
    experience_levels: Optional[List[str]] = Field(None, max_items=10)


class RecommendationRequest(BaseModel):
    candidate: CandidatePayload
    filters: Optional[FiltersRequest] = None
    top_k: Optional[int] = 10


class JobMatch(BaseModel):
    jobId: str
    jobTitle: str
    city: str
    province: str
    country: str
    locationScore: float
    titleScore: float
    experienceScore: float
    skillScore: float
    semanticScore: float
    finalScore: float


class RecommendationResponse(BaseModel):
    total_matches: int
    matches: List[JobMatch]


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str


class MessageResponse(BaseModel):
    message: str
