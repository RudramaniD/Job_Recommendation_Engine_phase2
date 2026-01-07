import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import pandas as pd
from ..core.text_processing import build_job_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QdrantVectorDB:
    def __init__(self, host: str = "localhost", port: int = 6333, collection_name: str = "job_embeddings"):
        # Validate inputs
        if not isinstance(host, str) or not host.strip():
            raise ValueError("Host must be a non-empty string")
        if not isinstance(port, int) or port <= 0 or port > 65535:
            raise ValueError("Invalid port number")
        
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', collection_name):
            raise ValueError("Invalid collection name")
        
        try:
            self.client = QdrantClient(host=host.strip(), port=port)
            self.collection_name = collection_name
            self.vector_size = 1024  # BAAI/bge-large-en-v1.5 dimension
        except Exception as e:
            logger.error(f"Qdrant client initialization failed: {e}")
            raise
        
    def _job_id_to_point_id(self, job_id: str) -> int:
        try:
            return int(hashlib.md5(job_id.encode()).hexdigest()[:8], 16)
        except Exception as e:
            logger.error(f"Failed to convert job_id {job_id} to point_id: {e}")
            raise ValueError(f"Invalid job_id format: {job_id}")
    
    def initialize_collection(self):
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )
            logger.info(f"Collection {self.collection_name} created successfully")
        except Exception as e:
            logger.debug(f"Collection {self.collection_name} already exists or creation failed: {e}")
    
    def upsert_job(self, job_id: str, job_data: Dict[str, Any], model: SentenceTransformer):
        if not job_id or not isinstance(job_id, str):
            raise ValueError("job_id must be a non-empty string")
        
        try:
            job_text = build_job_text(job_data)
            embedding = model.encode([job_text], convert_to_numpy=True)[0]
            
            point = PointStruct(
                id=self._job_id_to_point_id(job_id),
                vector=embedding.tolist(),
                payload={
                    "jobId": job_data.get("jobId"),
                    "jobTitle": job_data.get("jobTitle", ""),
                    "city": job_data.get("city", ""),
                    "province": job_data.get("province", ""),
                    "country": job_data.get("country", ""),
                    "skills": job_data.get("skills", []),
                    "jobSetting": job_data.get("jobSetting", []),
                    "positionType": job_data.get("positionType", ""),
                    "experienceLevel": job_data.get("experienceLevel", ""),
                    "activatedAt": str(job_data.get("activatedAt", "")),
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
        except Exception as e:
            logger.error(f"Failed to upsert job {job_id}: {e}")
            raise
    
    def bulk_upsert_jobs(self, jobs_df: pd.DataFrame, model: SentenceTransformer, batch_size: int = 50):
        if jobs_df.empty:
            return
        
        if batch_size <= 0 or batch_size > 1000:
            batch_size = 50  # Safe default

        try:
            job_texts = jobs_df.apply(build_job_text, axis=1).tolist()
            embeddings = model.encode(job_texts, batch_size=8, convert_to_numpy=True, show_progress_bar=True)
            
            points = []
            for idx, (_, job) in enumerate(jobs_df.iterrows()):
                point = PointStruct(
                    id=self._job_id_to_point_id(str(job.get("jobId"))),
                    vector=embeddings[idx].tolist(),
                    payload={
                        "jobId": job.get("jobId"),
                        "jobTitle": job.get("jobTitle", ""),
                        "city": job.get("city", ""),
                        "province": job.get("province", ""),
                        "country": job.get("country", ""),
                        "skills": job.get("skills", []),
                        "jobSetting": job.get("jobSetting", []),
                        "positionType": job.get("positionType", ""),
                        "experienceLevel": job.get("experienceLevel", ""),
                        "activatedAt": str(job.get("activatedAt", "")),
                    }
                )
                points.append(point)
                
                if len(points) >= batch_size:
                    self.client.upsert(collection_name=self.collection_name, points=points)
                    points = []
            
            if points:
                self.client.upsert(collection_name=self.collection_name, points=points)
                
        except Exception as e:
            logger.error(f"Failed to bulk upsert jobs: {e}")
            raise
    
    def search_similar_jobs(self, query_embedding: List[float], filters: Optional[Dict[str, Any]] = None, 
                           limit: int = 1000) -> List[Dict[str, Any]]:
        
        if limit <= 0 or limit > 10000:
            limit = 1000  # Safe default
        
        try:
            qdrant_filter = None
            if filters:
                conditions = []
                
                if filters.get("work_setting"):
                    for setting in filters["work_setting"]:
                        conditions.append(
                            FieldCondition(key="jobSetting", match=MatchValue(value=setting))
                        )
                 
                if filters.get("job_type"):
                    for job_type in filters["job_type"]:
                        conditions.append(
                            FieldCondition(key="positionType", match=MatchValue(value=job_type))
                        )
                
                if filters.get("experience_levels"):
                    for exp_level in filters["experience_levels"]:
                        conditions.append(
                            FieldCondition(key="experienceLevel", match=MatchValue(value=exp_level))
                        )
                
                if conditions:
                    qdrant_filter = Filter(should=conditions)
            
            # Use the correct query_points method for vector search
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                query_filter=qdrant_filter,
                limit=limit,
                with_payload=True
            )
            
            results = []
            # Access the points attribute of QueryResponse
            for hit in search_result.points:
                # hit is a ScoredPoint object with payload and score attributes
                job_data = hit.payload.copy()  # Make a copy to avoid modifying original
                job_data["semantic_score"] = hit.score
                results.append(job_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar jobs: {e}")
            return []
    
    def delete_job(self, job_id: str):
        """Delete job from collection"""
        if not job_id or not isinstance(job_id, str):
            raise ValueError("job_id must be a non-empty string")
        
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[self._job_id_to_point_id(job_id)]
            )
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            return self.client.get_collection(self.collection_name)
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}