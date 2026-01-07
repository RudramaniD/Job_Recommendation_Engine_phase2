"""
Real-time job creation hook for immediate VectorDB updates
This module provides functions to integrate with job creation workflow
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.engine.qdrant_recommendation_engine import QdrantRecommendationEngine
from src.core.layer0_validation import validate_job_record
from config.settings import *

# Global engine instance (initialized once)
_engine = None

def get_engine():
    """Get or create QdrantRecommendationEngine instance"""
    global _engine
    if _engine is None:
        config = {
            "MONGO_URI": MONGO_URI,
            "DB_NAME": DB_NAME,
            "JOBS_COLLECTION": JOBS_COLLECTION,
            "EMBEDDING_MODEL": EMBEDDING_MODEL,
            "QDRANT_HOST": "localhost",
            "QDRANT_PORT": 6333,
            "QDRANT_COLLECTION": "job_embeddings",
        }
        _engine = QdrantRecommendationEngine(config)
    return _engine

def create_job_with_vectordb(job_data: dict) -> str:
    """
    Create job in MongoDB AND immediately add to VectorDB
    
    Usage in job creation API:
    ```python
    from scripts.realtime_job_hooks import create_job_with_vectordb
    
    def create_job_endpoint(job_data):
        job_id = create_job_with_vectordb(job_data)
        return {"job_id": job_id, "status": "created"}
    ```
    """
    
    # Step 1: Validate job data (Layer 0)
    validated_job = validate_job_record(job_data)
    if not validated_job:
        raise ValueError("Job validation failed")
    
    # Step 2: Save to MongoDB (your existing logic)
    # job_id = save_to_mongodb(validated_job)  # Your existing function
    job_id = validated_job.get("jobId")
    
    # Step 3: Immediately add to VectorDB for real-time availability
    try:
        engine = get_engine()
        engine.add_new_job_to_vectordb(validated_job)
        print(f"✅ Job {job_id} added to VectorDB in real-time")
    except Exception as e:
        print(f"⚠️ VectorDB update failed for job {job_id}: {e}")
        # Job still exists in MongoDB, VectorDB can be synced later
    
    return job_id

def update_job_in_vectordb(job_id: str, updated_job_data: dict):
    """
    Update job in VectorDB when job is modified
    
    Usage:
    ```python
    def update_job_endpoint(job_id, updates):
        # Update in MongoDB first
        updated_job = update_job_in_mongodb(job_id, updates)
        
        # Update in VectorDB
        update_job_in_vectordb(job_id, updated_job)
    ```
    """
    
    validated_job = validate_job_record(updated_job_data)
    if not validated_job:
        raise ValueError("Job validation failed")
    
    try:
        engine = get_engine()
        engine.add_new_job_to_vectordb(validated_job)  # Upsert operation
        print(f"✅ Job {job_id} updated in VectorDB")
    except Exception as e:
        print(f"⚠️ VectorDB update failed for job {job_id}: {e}")

def delete_job_from_vectordb(job_id: str):
    """
    Delete job from VectorDB when job is deactivated
    
    Usage:
    ```python
    def deactivate_job_endpoint(job_id):
        # Deactivate in MongoDB
        deactivate_job_in_mongodb(job_id)
        
        # Remove from VectorDB
        delete_job_from_vectordb(job_id)
    ```
    """
    
    try:
        engine = get_engine()
        engine.vectordb.delete_job(job_id)
        print(f"✅ Job {job_id} removed from VectorDB")
    except Exception as e:
        print(f"⚠️ VectorDB deletion failed for job {job_id}: {e}")

def sync_mongodb_to_vectordb():
    """
    Sync all MongoDB jobs to VectorDB (for maintenance/recovery)
    
    Usage:
    ```python
    # Run as scheduled job or manual sync
    sync_mongodb_to_vectordb()
    ```
    """
    
    try:
        engine = get_engine()
        engine.migrate_jobs_to_vectordb()
        print("✅ MongoDB → VectorDB sync completed")
    except Exception as e:
        print(f"⚠️ Sync failed: {e}")

# Example integration with existing job creation workflow
def example_job_creation_integration():
    """
    Example of how to integrate with existing job creation system
    """
    
    # Simulate job creation request
    new_job_data = {
        "jobId": "R-0000999999",
        "jobTitle": "Senior Python Developer",
        "status": "ACTIVE",
        "city": "Toronto",
        "province": "Ontario", 
        "country": "Canada",
        "skills": ["Python", "Django", "PostgreSQL"],
        "jobSetting": ["REMOTE"],
        "positionType": "FULLTIME",
        "experienceLevel": "Senior",
        "jobDescription": "We are looking for a senior Python developer...",
    }
    
    # Create job with real-time VectorDB update
    job_id = create_job_with_vectordb(new_job_data)
    print(f"Job {job_id} created and immediately available for recommendations!")

if __name__ == "__main__":
    example_job_creation_integration()