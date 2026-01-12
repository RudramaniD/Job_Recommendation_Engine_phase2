import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from sentence_transformers import SentenceTransformer

from ..database.mongodb_client import connect_mongo, load_all_active_jobs
from ..database.qdrant_client import QdrantVectorDB
from ..core.layer0_validation import validate_candidate_input
from ..core.layer1_constraints import apply_layer1_eligibility_filter
from ..core.text_processing import build_candidate_text
from ..core.scoring import location_score_fn, title_score_fn, experience_score_fn, jaccard_skill_overlap, check_role_affinity

logger = logging.getLogger(__name__)

class QdrantRecommendationEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model: Optional[SentenceTransformer] = None
        self.vectordb = QdrantVectorDB(
            host=config.get("QDRANT_HOST", "localhost"),
            port=config.get("QDRANT_PORT", 6333),
            collection_name=config.get("QDRANT_COLLECTION", "job_embeddings")
        )
        
    def get_embedding_model(self) -> SentenceTransformer:
        if self.model is None:
            self.model = SentenceTransformer(self.config["EMBEDDING_MODEL"])
        return self.model
    
    def initialize_vectordb(self):
        self.vectordb.initialize_collection()
    
    def migrate_jobs_to_vectordb(self):
        client = connect_mongo(self.config["MONGO_URI"])
        jobs_df = load_all_active_jobs(client, self.config["DB_NAME"], self.config["JOBS_COLLECTION"])
        
        if jobs_df.empty:
            return
        
        model = self.get_embedding_model()
        self.vectordb.bulk_upsert_jobs(jobs_df, model)
    
    def add_new_job_to_vectordb(self, job_data: Dict[str, Any]):
        model = self.get_embedding_model()
        job_id = str(job_data.get("jobId"))
        self.vectordb.upsert_job(job_id, job_data, model)

    def update_job_in_vectordb(self, job_id: str, job_data: Dict[str, Any]):
        if not job_data or not isinstance(job_data, dict):
            raise ValueError("job_data must be a non-empty dictionary")

        if not job_id:
            raise ValueError("job_id must be provided")

        try:
            model = self.get_embedding_model()
            self.vectordb.upsert_job(str(job_id), job_data, model)
            logger.info(f"Successfully updated job {job_id} in Qdrant Db")
        except Exception as e:
            logger.error(f"Failed to update job: {e}")
            raise
    
    def match_jobs_for_candidate(self, candidate: Dict[str, Any], 
                                filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        validated_candidate = validate_candidate_input(candidate)
        
        model = self.get_embedding_model()
        candidate_text = build_candidate_text(validated_candidate)
        candidate_embedding = model.encode([candidate_text], convert_to_numpy=True)[0]
        
        similar_jobs = self.vectordb.search_similar_jobs(
            query_embedding=candidate_embedding.tolist(),
            filters=filters,
            limit=1000
        )
        
        if not similar_jobs:
            return {"total_matches": 0, "matches": []}
        
        jobs_df = pd.DataFrame(similar_jobs)
        
        eligible_jobs_df = apply_layer1_eligibility_filter(jobs_df, validated_candidate)
        
        if eligible_jobs_df.empty:
            return {"total_matches": 0, "matches": []}
        
        candidate_skills = validated_candidate.get("skills", "")
        candidate_title = validated_candidate.get("desired_title", 
                            validated_candidate.get("jobTitle", 
                                validated_candidate.get("headline", "")))
        matches = []
        
        for _, job_row in eligible_jobs_df.iterrows():
            loc_score = location_score_fn(
                validated_candidate.get("city"),
                validated_candidate.get("province"),
                validated_candidate.get("country"),
                job_row.get("city"),
                job_row.get("province"),
                job_row.get("country"),
            )
            
            job_title = job_row.get("jobTitle", "")
            title_score = title_score_fn(candidate_title, job_title)
            
            exp_score = experience_score_fn(
                validated_candidate.get("experience", ""),
                job_row.get("experienceLevel", ""),
            )
            
            skill_score = jaccard_skill_overlap(candidate_skills, job_row.get("skills", []))
            semantic_score = float(job_row.get("semantic_score", 0.0))
            
            role_affinity = check_role_affinity(candidate_title, job_title)
            
            final_score = (
                0.4 * loc_score
                + 0.3 * title_score
                + 0.2 * exp_score
                + 0.1 * skill_score
                + 0.05 * semantic_score
            )
            
            if skill_score == 0.0:
                final_score = final_score * 0.5
            
            if role_affinity < 0.5:
                final_score = final_score * 0.3
            
            matches.append({
                "jobId": job_row.get("jobId"),
                "jobTitle": job_title,
                "city": job_row.get("city", ""),
                "province": job_row.get("province", ""),
                "country": job_row.get("country", ""),
                "locationScore": round(loc_score, 4),
                "titleScore": round(title_score, 4),
                "experienceScore": round(exp_score, 4),
                "skillScore": round(skill_score, 4),
                "semanticScore": round(semantic_score, 4),
                "finalScore": round(final_score, 4),
            })
        
        matches = sorted(matches, key=lambda x: x["finalScore"], reverse=True)
        return {"total_matches": len(matches), "matches": matches}
    
    def get_vectordb_stats(self) -> Dict[str, Any]:
        return self.vectordb.get_collection_info()