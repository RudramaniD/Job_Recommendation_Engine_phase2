import pandas as pd
from typing import Dict, List, Any, Optional
from sentence_transformers import SentenceTransformer

from ..database.mongodb_client import connect_mongo, load_all_active_jobs
from ..database.qdrant_client import QdrantVectorDB
from ..core.layer0_validation import validate_candidate_input
from ..core.layer1_constraints import apply_layer1_eligibility_filter
from ..core.text_processing import build_candidate_text
from ..core.scoring import location_score_fn, title_score_fn, experience_score_fn, jaccard_skill_overlap

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
        """Initialize Qdrant collection"""
        self.vectordb.initialize_collection()
    
    def migrate_jobs_to_vectordb(self):
        """One-time migration: Load all jobs from MongoDB to Qdrant"""
        client = connect_mongo(self.config["MONGO_URI"])
        jobs_df = load_all_active_jobs(client, self.config["DB_NAME"], self.config["JOBS_COLLECTION"])
        
        if jobs_df.empty:
            return
        
        model = self.get_embedding_model()
        self.vectordb.bulk_upsert_jobs(jobs_df, model)
    
    def add_new_job_to_vectordb(self, job_data: Dict[str, Any]):
        """Real-time: Add new job to Qdrant immediately"""
        model = self.get_embedding_model()
        job_id = str(job_data.get("jobId"))
        self.vectordb.upsert_job(job_id, job_data, model)
    
    def match_jobs_for_candidate(self, candidate: Dict[str, Any], 
                                filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        validated_candidate = validate_candidate_input(candidate)
        
        # Generate candidate embedding
        model = self.get_embedding_model()
        candidate_text = build_candidate_text(validated_candidate)
        candidate_embedding = model.encode([candidate_text], convert_to_numpy=True)[0]
        
        # Search Qdrant for similar jobs (with native filtering)
        similar_jobs = self.vectordb.search_similar_jobs(
            query_embedding=candidate_embedding.tolist(),
            filters=filters,
            limit=1000
        )
        
        if not similar_jobs:
            return {"total_matches": 0, "matches": []}
        
        # Convert to DataFrame for layer 1 filtering
        jobs_df = pd.DataFrame(similar_jobs)
        
        # Apply layer 1 eligibility constraints
        eligible_jobs_df = apply_layer1_eligibility_filter(jobs_df, validated_candidate)
        
        if eligible_jobs_df.empty:
            return {"total_matches": 0, "matches": []}
        
        # Calculate final scores
        candidate_skills = validated_candidate.get("skills", "")
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
            
            title_score = title_score_fn(
                validated_candidate.get("desired_title", 
                    validated_candidate.get("jobTitle", 
                        validated_candidate.get("headline", ""))),
                job_row.get("jobTitle", ""),
            )
            
            exp_score = experience_score_fn(
                validated_candidate.get("experience", ""),
                job_row.get("experienceLevel", ""),
            )
            
            skill_score = jaccard_skill_overlap(candidate_skills, job_row.get("skills", []))
            semantic_score = float(job_row.get("semantic_score", 0.0))
            
            final_score = (
                0.4 * loc_score
                + 0.3 * title_score
                + 0.2 * exp_score
                + 0.1 * skill_score
                + 0.05 * semantic_score
            )
            
            matches.append({
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
            })
        
        matches = sorted(matches, key=lambda x: x["finalScore"], reverse=True)
        return {"total_matches": len(matches), "matches": matches}
    
    def get_vectordb_stats(self) -> Dict[str, Any]:
        return self.vectordb.get_collection_info()