import logging
import pandas as pd
from pymongo import MongoClient
from typing import List, Dict, Any
from ..core.layer0_validation import validate_job_record

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_mongo(mongo_uri: str) -> MongoClient:
    try:
        # Validate URI format
        if not mongo_uri or not isinstance(mongo_uri, str) or not mongo_uri.startswith(('mongodb://', 'mongodb+srv://')):
            raise ValueError("Invalid MongoDB URI format")
        
        client = MongoClient(
            mongo_uri, 
            serverSelectionTimeoutMS=5000,
            maxPoolSize=10,  # Limit connection pool
            retryWrites=True
        )
        client.server_info()
        logger.info("MongoDB connection established successfully")
        return client
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise

def load_all_active_jobs(client: MongoClient, db_name: str, collection_name: str) -> pd.DataFrame:
    if not isinstance(db_name, str) or not db_name.strip():
        raise ValueError("Database name must be a non-empty string")
    if not isinstance(collection_name, str) or not collection_name.strip():
        raise ValueError("Collection name must be a non-empty string")
    
    try:
        db = client[db_name]
        coll = db[collection_name]
        docs = list(coll.find({"status": "ACTIVE"}))
        if not docs:
            return pd.DataFrame()
        
        valid_jobs = []
        for doc in docs:
            validated_job = validate_job_record(doc)
            if validated_job is not None:
                valid_jobs.append(validated_job)

        if not valid_jobs:
            return pd.DataFrame()

        jobs_df = pd.DataFrame(valid_jobs)
        if "jobId" not in jobs_df.columns:
            raise ValueError("jobId field is missing in jobs documents")
        jobs_df["jobId"] = jobs_df["jobId"].astype(str)
        if "_id" in jobs_df.columns:
            jobs_df["_id"] = jobs_df["_id"].astype(str)
        return jobs_df
    except Exception as e:
        logger.error(f"Failed to load jobs from MongoDB: {e}")
        raise
