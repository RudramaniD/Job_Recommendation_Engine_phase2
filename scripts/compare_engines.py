import time
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.engine.recommendation_engine import JobRecommendationEngine  # FAISS
from src.engine.qdrant_recommendation_engine import QdrantRecommendationEngine  # Qdrant
from config.settings import *

def compare_faiss_vs_qdrant():
    """Side-by-side comparison of FAISS vs Qdrant performance"""
    
    config = {
        "MONGO_URI": MONGO_URI,
        "DB_NAME": DB_NAME,
        "JOBS_COLLECTION": JOBS_COLLECTION,
        "EMBEDDING_MODEL": EMBEDDING_MODEL,
        "CACHE_DIR": CACHE_DIR,
        "CACHE_DURATION_MINUTES": CACHE_DURATION_MINUTES,
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": 6333,
        "QDRANT_COLLECTION": "job_embeddings",
    }
    
    # Test candidate
    test_candidate = {
        "candidate_id": "comparison_test",
        "headline": "Customer Experience Manager | Customer Success Manager",
        "desired_title": "Training Specialist",
        "skills": "Customer Success,Client Management, Communication",
        "summary": "Customer Success professional focused on building strong relationships with enterprise clients.",
        "experience": "3+ years in customer success and account management in SaaS environments.",
        "city": "Ottawa",
        "province": "Ontario",
        "country": "Canada",
    }
    
    test_filters = {
        "work_setting": ["HYBRID", "REMOTE"],
        "job_type": ["FULLTIME"],
    }
    
    print("🔥 FAISS vs QDRANT PERFORMANCE COMPARISON")
    print("=" * 60)
    
    # Test FAISS Engine
    print("\n🐌 Testing FAISS Engine (Old Implementation)...")
    faiss_engine = JobRecommendationEngine(config)
    
    start_time = time.time()
    faiss_result = faiss_engine.match_jobs_for_candidate(test_candidate, test_filters)
    faiss_time = time.time() - start_time
    
    print(f"   Time: {faiss_time:.3f} seconds")
    print(f"   Results: {faiss_result['total_matches']} matches")
    print(f"   Top result: {faiss_result['matches'][0]['jobTitle'] if faiss_result['matches'] else 'None'}")
    
    # Test Qdrant Engine
    print("\n⚡ Testing Qdrant Engine (New Implementation)...")
    qdrant_engine = QdrantRecommendationEngine(config)
    
    start_time = time.time()
    qdrant_result = qdrant_engine.match_jobs_for_candidate(test_candidate, test_filters)
    qdrant_time = time.time() - start_time
    
    print(f"   Time: {qdrant_time:.3f} seconds")
    print(f"   Results: {qdrant_result['total_matches']} matches")
    print(f"   Top result: {qdrant_result['matches'][0]['jobTitle'] if qdrant_result['matches'] else 'None'}")
    
    # Performance Comparison
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON RESULTS")
    print("=" * 60)
    
    improvement = faiss_time / qdrant_time if qdrant_time > 0 else float('inf')
    
    print(f"FAISS Engine:    {faiss_time:.3f} seconds")
    print(f"Qdrant Engine:   {qdrant_time:.3f} seconds")
    print(f"Speed Improvement: {improvement:.0f}x faster!")
    
    # Results Quality Comparison
    print(f"\nRESULTS QUALITY:")
    print(f"FAISS Results:   {faiss_result['total_matches']} matches")
    print(f"Qdrant Results:  {qdrant_result['total_matches']} matches")
    
    # Compare top 5 results
    print(f"\nTOP 5 RESULTS COMPARISON:")
    print(f"{'Rank':<4} {'FAISS Job Title':<30} {'Qdrant Job Title':<30}")
    print("-" * 70)
    
    for i in range(min(5, len(faiss_result['matches']), len(qdrant_result['matches']))):
        faiss_job = faiss_result['matches'][i]['jobTitle'][:28]
        qdrant_job = qdrant_result['matches'][i]['jobTitle'][:28]
        print(f"{i+1:<4} {faiss_job:<30} {qdrant_job:<30}")
    
    # Scalability Analysis
    print(f"\nSCALABILITY ANALYSIS:")
    concurrent_faiss = max(1, int(60 / faiss_time))  # Requests per minute
    concurrent_qdrant = max(1, int(60 / qdrant_time))  # Requests per minute
    
    print(f"FAISS Capacity:   ~{concurrent_faiss} requests/minute")
    print(f"Qdrant Capacity:  ~{concurrent_qdrant} requests/minute")
    print(f"Capacity Improvement: {concurrent_qdrant/concurrent_faiss:.0f}x more users")
    
    # Recommendation
    print(f"\n🎯 RECOMMENDATION:")
    if improvement > 10:
        print("✅ MIGRATE TO QDRANT - Significant performance improvement!")
        print("✅ Production-ready for high-traffic applications")
        print("✅ Supports real-time job updates")
    else:
        print("⚠️  Consider keeping FAISS for low-traffic scenarios")
    
    return {
        "faiss_time": faiss_time,
        "qdrant_time": qdrant_time,
        "improvement": improvement,
        "faiss_results": faiss_result['total_matches'],
        "qdrant_results": qdrant_result['total_matches']
    }

if __name__ == "__main__":
    compare_faiss_vs_qdrant()