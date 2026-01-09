import logging
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    RecommendationRequest,
    RecommendationResponse,
    HealthResponse,
    MessageResponse
)

from .middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware
from ..engine.qdrant_recommendation_engine import QdrantRecommendationEngine
from config.settings import *

logging.basicConfig(
    level = logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title ="Job Recommendation Engine",
    description = "AI-powered recommendation engine using QDrant Vector DB",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

config = {
    "MONGO_URI": MONGO_URI,
    "DB_NAME": DB_NAME,
    "JOBS_COLLECTION": JOBS_COLLECTION,
    "EMBEDDING_MODEL": EMBEDDING_MODEL,
    "QDRANT_HOST": "localhost",
    "QDRANT_PORT": 6333,
    "QDRANT_COLLECTION": "job_embeddings",
}

try:
    engine = QdrantRecommendationEngine(config)
    logger.info("Recommendation engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize recommendation engine: {e}")
    raise

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "Healthy",
        "service": "job-recommendation-engine",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/v1/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    try:
        candidate_dict = request.candidate.dict(exclude_none=True)
        
        filters_dict = None
        if request.filters:
            filters_dict = request.filters.dict(exclude_none=True)
        elif request.candidate.jobPreferences:
            prefs = request.candidate.jobPreferences
            filters_dict = {}
            if prefs.workSetting:
                # Normalize to uppercase to match MongoDB format
                filters_dict["work_setting"] = [ws.upper() for ws in prefs.workSetting]
            if prefs.workType:
                # Normalize: "Full-Time" -> "FULLTIME", "Part-Time" -> "PARTTIME"
                normalized_type = prefs.workType.upper().replace("-", "").replace("_", "")
                filters_dict["job_type"] = [normalized_type]
        
        logger.info(f"Processing recommendation for candidate: {candidate_dict.get('_id') or candidate_dict.get('candidate_id')}")
        logger.info(f"Applied filters: {filters_dict}")
        
        result = engine.match_jobs_for_candidate(candidate_dict, filters_dict)
        
        if request.top_k and request.top_k < len(result['matches']):
            result['matches'] = result['matches'][:request.top_k]
        
        logger.info(f"Found {result['total_matches']} matches, returning top {len(result['matches'])}")
        
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Job matching failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/api/v1/stats")
async def get_stats():
    try:
        stats = engine.get_vectordb_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@app.post("/api/v1/admin/initialize", response_model=MessageResponse)
async def initialize_vectordb():
    try:
        engine.initialize_vectordb()
        logger.info("VectorDB initialized successfully")
        return {"message": "VectorDB initialized successfully"}
    except Exception as e:
        logger.error(f"VectorDB initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="VectorDB initialization failed"
        )


@app.post("/api/v1/admin/migrate", response_model=MessageResponse)
async def migrate_jobs():
    try:
        logger.info("Starting job migration...")
        engine.migrate_jobs_to_vectordb()
        logger.info("Job migration completed successfully")
        return {"message": "Jobs migrated successfully"}
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Migration failed"
        )
