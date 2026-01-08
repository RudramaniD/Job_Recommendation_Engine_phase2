import time
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.engine.recommendation_engine import JobRecommendationEngine
from config.settings import *

def benchmark_recommendation_engine():
    """Benchmark the job recommendation engine performance"""
    
    config = {
        "MONGO_URI": MONGO_URI,
        "DB_NAME": DB_NAME,
        "JOBS_COLLECTION": JOBS_COLLECTION,
        "EMBEDDING_MODEL": EMBEDDING_MODEL,
        "CACHE_DIR": CACHE_DIR,
        "CACHE_DURATION_MINUTES": CACHE_DURATION_MINUTES,
    }
    
    engine = JobRecommendationEngine(config)
    
    # Test candidate from the notebook
    test_candidate = {
        "candidate_id": "benchmark_test",
        "headline": "Customer Experience Manager | Customer Success Manager",
        "desired_title": "Training Specialist",
        "skills": "Customer Success,Client Management, Communication",
        "summary": "Customer Success / Customer Experience professional focused on building strong relationships with enterprise clients and driving adoption of AI-powered SaaS products.",
        "experience": "3+ years in customer success and account management in SaaS and B2B environments, working closely with sales and product teams to track usage metrics and improve client outcomes.",
        "city": "Ottawa",
        "province": "Ontario",
        "country": "Canada",
    }
    
    test_filters = {
        "work_setting": ["HYBRID", "REMOTE"],
        "job_type": ["FULLTIME"],
    }
    
    print("=" * 60)
    print("JOB RECOMMENDATION ENGINE BENCHMARK")
    print("=" * 60)
    
    # Benchmark initial load (cache build)
    print("\n1. Initial Load (Building Vector Cache)...")
    start_time = time.time()
    result = engine.match_jobs_for_candidate(test_candidate, test_filters)
    initial_load_time = time.time() - start_time
    
    print(f"   Time: {initial_load_time:.2f} seconds")
    print(f"   Total matches: {result['total_matches']}")
    
    # Benchmark subsequent queries (cache hit)
    print("\n2. Subsequent Query (Cache Hit)...")
    start_time = time.time()
    result = engine.match_jobs_for_candidate(test_candidate, test_filters)
    cache_hit_time = time.time() - start_time
    
    print(f"   Time: {cache_hit_time:.2f} seconds")
    print(f"   Total matches: {result['total_matches']}")
    
    # Show top 5 results
    print(f"\n3. Top 5 Results:")
    for i, match in enumerate(result["matches"][:5], 1):
        print(f"   {i}. {match['jobId']} - {match['jobTitle']}")
        print(f"      Location: {match['city']}, {match['province']}, {match['country']}")
        print(f"      Final Score: {match['finalScore']}")
        print(f"      Breakdown: Loc:{match['locationScore']}, Title:{match['titleScore']}, "
              f"Exp:{match['experienceScore']}, Skills:{match['skillScore']}, "
              f"Semantic:{match['semanticScore']}")
        print()
    
    # Performance summary
    print("=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"Initial Load Time: {initial_load_time:.2f}s")
    print(f"Cache Hit Time: {cache_hit_time:.2f}s")
    print(f"Speed Improvement: {initial_load_time/cache_hit_time:.1f}x faster")
    print(f"Total Jobs Processed: {result['total_matches']}")
    
    # Test multiple candidates for throughput
    print(f"\n4. Throughput Test (10 queries)...")
    start_time = time.time()
    for i in range(10):
        test_candidate["candidate_id"] = f"throughput_test_{i}"
        engine.match_jobs_for_candidate(test_candidate, test_filters)
    throughput_time = time.time() - start_time
    
    print(f"   Total time for 10 queries: {throughput_time:.2f}s")
    print(f"   Average time per query: {throughput_time/10:.3f}s")
    print(f"   Queries per second: {10/throughput_time:.1f}")

if __name__ == "__main__":
    benchmark_recommendation_engine()
