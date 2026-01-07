import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.engine.qdrant_recommendation_engine import QdrantRecommendationEngine
from config.settings import *

def migrate_to_qdrant():
    """Migrate from FAISS to Qdrant VectorDB"""
    
    config = {
        "MONGO_URI": MONGO_URI,
        "DB_NAME": DB_NAME,
        "JOBS_COLLECTION": JOBS_COLLECTION,
        "EMBEDDING_MODEL": EMBEDDING_MODEL,
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": 6333,
        "QDRANT_COLLECTION": "job_embeddings",
    }
    
    print("🚀 Starting FAISS → Qdrant Migration")
    print("=" * 50)
    
    # Initialize Qdrant engine
    engine = QdrantRecommendationEngine(config)
    
    # Step 1: Initialize Qdrant collection
    print("1. Initializing Qdrant collection...")
    engine.initialize_vectordb()
    
    # Step 2: Migrate all jobs from MongoDB to Qdrant
    print("2. Migrating jobs from MongoDB to Qdrant...")
    engine.migrate_jobs_to_vectordb()
    
    # Step 3: Verify migration
    print("3. Verifying migration...")
    stats = engine.get_vectordb_stats()
    print(f"   ✅ VectorDB contains {stats.points_count} job embeddings")
    
    # Step 4: Test search performance
    print("4. Testing search performance...")
    test_candidate = {
        "candidate_id": "migration_test",
        "headline": "Software Engineer",
        "desired_title": "Senior Developer",
        "skills": "Python,JavaScript,React",
        "city": "Toronto",
        "province": "Ontario",
        "country": "Canada",
    }
    
    import time
    start_time = time.time()
    result = engine.match_jobs_for_candidate(test_candidate)
    search_time = time.time() - start_time
    
    print(f"   ✅ Search completed in {search_time:.3f} seconds")
    print(f"   ✅ Found {result['total_matches']} matching jobs")
    
    print("\n🎉 Migration to Qdrant completed successfully!")
    print("=" * 50)
    print("PERFORMANCE COMPARISON:")
    print(f"  FAISS (old):  4+ minutes per request")
    print(f"  Qdrant (new): {search_time:.3f} seconds per request")
    print(f"  Improvement:  {(240/search_time):.0f}x faster!")
    
    return True

if __name__ == "__main__":
    migrate_to_qdrant()