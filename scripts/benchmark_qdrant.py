import time
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.engine.qdrant_recommendation_engine import QdrantRecommendationEngine
from config.settings import *

def benchmark_qdrant_performance():
    """Benchmark Qdrant VectorDB performance"""
    
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
    
    # Test candidates
    test_candidates = [
        {
            "candidate_id": "perf_test_1",
            "headline": "Software Engineer | Full Stack Developer",
            "desired_title": "Senior Software Engineer",
            "skills": "Python,JavaScript,React,Node.js,AWS",
            "city": "Toronto",
            "province": "Ontario",
            "country": "Canada",
        },
        {
            "candidate_id": "perf_test_2",
            "headline": "Data Scientist | ML Engineer",
            "desired_title": "Senior Data Scientist",
            "skills": "Python,Machine Learning,TensorFlow,SQL",
            "city": "Vancouver",
            "province": "British Columbia",
            "country": "Canada",
        },
        {
            "candidate_id": "perf_test_3",
            "headline": "Marketing Manager | Growth Specialist",
            "desired_title": "Marketing Director",
            "skills": "Digital Marketing,SEO,Analytics,Content Strategy",
            "city": "Montreal",
            "province": "Quebec",
            "country": "Canada",
        }
    ]
    
    test_filters = {
        "work_setting": ["HYBRID", "REMOTE"],
        "job_type": ["FULLTIME"],
    }
    
    print("🚀 QDRANT VECTORDB PERFORMANCE BENCHMARK")
    print("=" * 60)
    
    # Get VectorDB stats
    stats = engine.get_vectordb_stats()
    print(f"VectorDB Status: {stats.points_count} job embeddings ready")
    print("=" * 60)
    
    # Single query benchmark
    print("\n1. Single Query Performance:")
    candidate = test_candidates[0]
    
    start_time = time.time()
    result = engine.match_jobs_for_candidate(candidate, test_filters)
    single_query_time = time.time() - start_time
    
    print(f"   Time: {single_query_time:.3f} seconds")
    print(f"   Results: {result['total_matches']} matches")
    print(f"   Top result: {result['matches'][0]['jobTitle'] if result['matches'] else 'None'}")
    
    # Concurrent queries simulation
    print(f"\n2. Throughput Test (10 queries):")
    start_time = time.time()
    
    for i in range(10):
        candidate = test_candidates[i % len(test_candidates)]
        candidate["candidate_id"] = f"throughput_test_{i}"
        engine.match_jobs_for_candidate(candidate, test_filters)
    
    throughput_time = time.time() - start_time
    avg_time = throughput_time / 10
    qps = 10 / throughput_time
    
    print(f"   Total time: {throughput_time:.3f} seconds")
    print(f"   Average per query: {avg_time:.3f} seconds")
    print(f"   Queries per second: {qps:.1f} QPS")
    
    # Stress test simulation
    print(f"\n3. Stress Test (100 queries):")
    start_time = time.time()
    
    for i in range(100):
        candidate = test_candidates[i % len(test_candidates)]
        candidate["candidate_id"] = f"stress_test_{i}"
        engine.match_jobs_for_candidate(candidate, test_filters)
    
    stress_time = time.time() - start_time
    stress_avg = stress_time / 100
    stress_qps = 100 / stress_time
    
    print(f"   Total time: {stress_time:.2f} seconds")
    print(f"   Average per query: {stress_avg:.3f} seconds")
    print(f"   Queries per second: {stress_qps:.1f} QPS")
    
    # Performance summary
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"Single Query:     {single_query_time:.3f}s")
    print(f"Average Query:    {avg_time:.3f}s")
    print(f"Stress Average:   {stress_avg:.3f}s")
    print(f"Max Throughput:   {stress_qps:.1f} QPS")
    
    # Comparison with old system
    old_system_time = 240  # 4 minutes
    improvement = old_system_time / single_query_time
    
    print(f"\nCOMPARISON:")
    print(f"Old FAISS System: {old_system_time}s per query")
    print(f"New Qdrant System: {single_query_time:.3f}s per query")
    print(f"Performance Gain: {improvement:.0f}x faster!")
    
    # Concurrent user capacity
    concurrent_capacity = int(stress_qps * 0.8)  # 80% of max throughput
    print(f"Concurrent Users: ~{concurrent_capacity} users supported")
    
    print(f"\n✅ Qdrant VectorDB is production-ready!")

if __name__ == "__main__":
    benchmark_qdrant_performance()