import faiss
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from sentence_transformers import SentenceTransformer

from ..database.mongodb_client import connect_mongo, load_all_active_jobs
from ..database.vectordb_client import VectorDBCache
from ..engine.filters import apply_filters_on_dataframe
from ..core.layer0_validation import validate_candidate_input
from ..core.layer1_constraints import apply_layer1_eligibility_filter
from ..core.text_processing import build_candidate_text
from ..core.scoring import location_score_fn, title_score_fn, experience_score_fn, jaccard_skill_overlap

class JobRecommendationEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model: Optional[SentenceTransformer] = None
        self.vector_cache = VectorDBCache(
            config["CACHE_DIR"], 
            config["CACHE_DURATION_MINUTES"]
        )

    def get_embedding_model(self) -> SentenceTransformer:
        if self.model is None:
            self.model = SentenceTransformer(self.config["EMBEDDING_MODEL"])
        return self.model

    def match_jobs_for_candidate(self, candidate: Dict[str, Any], 
                                filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        validated_candidate = validate_candidate_input(candidate)
        client = connect_mongo(self.config["MONGO_URI"])
        
        # Load jobs from MongoDB
        jobs_df = load_all_active_jobs(client, self.config["DB_NAME"], self.config["JOBS_COLLECTION"])
        
        if jobs_df.empty:
            return {"total_matches": 0, "matches": []}

        # Get or build vector index
        model = self.get_embedding_model()
        index, jobs_df = self.vector_cache.get_or_build(
            client, self.config["DB_NAME"], self.config["JOBS_COLLECTION"], jobs_df, model
        )

        # Apply filters
        filtered_jobs_df = apply_filters_on_dataframe(jobs_df, filters)
        if filtered_jobs_df.empty:
            return {"total_matches": 0, "matches": []}
        
        # Apply layer 1 eligibility constraints
        eligible_jobs_df = apply_layer1_eligibility_filter(filtered_jobs_df, validated_candidate)
        if eligible_jobs_df.empty:
            return {"total_matches": 0, "matches": []}
        
        # Generate candidate embedding
        candidate_text = build_candidate_text(validated_candidate)
        cand_emb = model.encode([candidate_text], convert_to_numpy=True, show_progress_bar=False)
        faiss.normalize_L2(cand_emb)

        # Perform semantic search
        filtered_indices = filtered_jobs_df.index.tolist()
        sim_scores, sim_indices = index.search(cand_emb, index.ntotal)
        sim_scores = sim_scores[0]
        sim_indices = sim_indices[0]

        filtered_results = [
            (score, idx)
            for score, idx in zip(sim_scores, sim_indices)
            if idx in filtered_indices
        ]

        # Calculate final scores
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
            semantic_score = float(score)

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
