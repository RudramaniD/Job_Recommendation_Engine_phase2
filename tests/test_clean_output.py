import sys
import os
import time
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.engine.qdrant_recommendation_engine import QdrantRecommendationEngine
from config.settings import *

def test_job_recommendations():
    
    config = {
        "MONGO_URI": MONGO_URI,
        "DB_NAME": DB_NAME,
        "JOBS_COLLECTION": JOBS_COLLECTION,
        "EMBEDDING_MODEL": EMBEDDING_MODEL,
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": 6333,
        "QDRANT_COLLECTION": "job_embeddings",
    }
    
    engine = QdrantRecommendationEngine(config)
    
    # Test candidate
    candidate = {
        "candidate_id": "1",
        "headline": "Customer Experience Manager | Customer Success Manager",
        "desired_title": "Training Specialist",
        "skills": " Customer Success,Client Management, Communication",
        "summary": "Customer Success / Customer Experience professional focused on building strong relationships with enterprise clients and driving adoption of AI-powered SaaS products.",
        "experience": "3+ years in customer success and account management in SaaS and B2B environments, working closely with sales and product teams to track usage metrics and improve client outcomes.",
        "location": "Ottawa, Ontario",
        "city": "Ottawa",
        "province": "Ontario",
        "country": "Canada",
        
    }
    
    filters = {
        "work_setting": ["HYBRID", "REMOTE"],
        "job_type": ["FULLTIME"],
    }
    
    # Get recommendations with timing
    start_time = time.time()
    result = engine.match_jobs_for_candidate(candidate, filters)
    end_time = time.time()
    
    recommendation_time = end_time - start_time
    
    # Display clean results
    print(f"Recommendation Time: {recommendation_time:.3f} seconds")
    print(f"Found {result['total_matches']} total matches")
    print("\n Top Job Recommendations:")
    
    for i, job in enumerate(result["matches"][:5], 1):
        print(f"{i}. {job['jobTitle']}")
        print(f" {job['city']}, {job['province']}, {job['country']}")
        print(f" Match Score: {job['finalScore']:.3f}")
        print(f" Job ID: {job['jobId']}")
        print()

if __name__ == "__main__":
    test_job_recommendations()