import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.recommendation_engine import JobRecommendationEngine
from config.settings import *

def migrate_to_vectordb():
    config = {
        "MONGO_URI" : MONGO_URI,
        "DB_NAME" : DB_NAME,
        "JOBS_COLLECTION" : JOBS_COLLECTION,
        "EMBEDDING_MODEL" : EMBEDDING_MODEL,
        "CACHE_DIR" : CACHE_DIR,
        "CACHE_DURATION_MINUTES" : CACHE_DURATION_MINUTES,
    }

    engine = JobRecommendationEngine(config)

    dummy_candidate = {"candidate_id":"migration_test"}
    engine.match_jobs_for_candidate(dummy_candidate)

    print("Migration to VectorDB completed!")

if __name__ == "__main__":
    migrate_to_vectordb()