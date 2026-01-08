import hashlib
import logging
import time
import subprocess
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
    def __init__(self, host: str = "localhost", port: int = 6333, collection_name: str = "job_embeddings", auto_start: bool = True):
        # Validate inputs
        if not isinstance(host, str) or not host.strip():
            raise ValueError("Host must be a non-empty string")
        if not isinstance(port, int) or port <= 0 or port > 65535:
            raise ValueError("Invalid port number")
        
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', collection_name):
            raise ValueError("Invalid collection name")
        
        self.host = host.strip()
        self.port = port
        self.collection_name = collection_name
        self.vector_size = 1024
        self.auto_start = auto_start
        self.client = None
        self.max_retries = 3
        
        self._connect()
    
    def _start_qdrant_server(self) -> bool:
        if not self.auto_start:
            return False
        
        try:
            logger.info("Attempting to start Qdrant server...")
            
            result = subprocess.run(
                ["docker", "ps", "-a", "-q", "-f", "name=qdrant"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout.strip():
                subprocess.run(["docker", "start", "qdrant"], check=True, timeout=10)
                logger.info("Started existing Qdrant container")
            else:
                subprocess.run([
                    "docker", "run", "-d",
                    "--name", "qdrant",
                    "-p", f"{self.port}:6333",
                    "-v", "qdrant_storage:/qdrant/storage:z",
                    "--restart", "unless-stopped",
                    "qdrant/qdrant:latest"
                ], check=True, timeout=30)
                logger.info("Created new Qdrant container")
            
            time.sleep(5)
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout while starting Qdrant server")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start Qdrant server: {e}")
            return False
        except FileNotFoundError:
            logger.error("Docker not found. Please install Docker or start Qdrant manually")
            return False
        except Exception as e:
            logger.error(f"Unexpected error starting Qdrant: {e}")
            return False
    
    def _connect(self, retry_count: int = 0) -> bool:
        try:
            self.client = QdrantClient(host=self.host, port=self.port, timeout=10)
            # Test connection
            self.client.get_collections()
            logger.info(f"Connected to Qdrant at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant (attempt {retry_count + 1}/{self.max_retries}): {e}")
            
            if retry_count < self.max_retries:
                # Try to start server on first failure
                if retry_count == 0 and self._start_qdrant_server():
                    time.sleep(3)
                    return self._connect(retry_count + 1)
                
                # Retry with exponential backoff
                wait_time = 2 ** retry_count
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                return self._connect(retry_count + 1)
            
            logger.error("Failed to connect to Qdrant after all retries")
            print("\n" + "="*80)
            print("QDRANT SERVER NOT RUNNING")
            print("="*80)
            print("\nQUICK START:")
            print("  1. Start Docker Desktop")
            print("  2. Run: docker run -d -p 6333:6333 --name qdrant qdrant/qdrant:latest")
            print("  3. Verify: curl http://localhost:6333/health")
            print("  4. Re-run your application")
            print("\n" + "="*80 + "\n")
            raise ConnectionError(f"Cannot connect to Qdrant at {self.host}:{self.port}. Please start Qdrant server.")
    
    def _ensure_connection(self):
        try:
            if self.client is None:
                self._connect()
            else:
                # Test connection
                self.client.get_collections()
        except Exception:
            logger.warning("Connection lost, attempting to reconnect...")
            self._connect()
        
    def _job_id_to_point_id(self, job_id: str) -> int:
        try:
            return int(hashlib.md5(job_id.encode()).hexdigest()[:8], 16)
        except Exception as e:
            logger.error(f"Failed to convert job_id {job_id} to point_id: {e}")
            raise ValueError(f"Invalid job_id format: {job_id}")
    
    def initialize_collection(self):
        self._ensure_connection()
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )
            logger.info(f"Collection {self.collection_name} created successfully")
        except Exception as e:
            logger.debug(f"Collection {self.collection_name} already exists or creation failed: {e}")
    
    def upsert_job(self, job_id: str, job_data: Dict[str, Any], model: SentenceTransformer):
        self._ensure_connection()
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
        self._ensure_connection()
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
        self._ensure_connection()
        
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
        self._ensure_connection()
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
        self._ensure_connection()
        try:
            return self.client.get_collection(self.collection_name)
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}