import pickle
import faiss
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import Tuple, Optional
from ..core.text_processing import build_job_text

class VectorDBCache:
    def __init__(self, cache_dir: Path, cache_duration_minutes: int):
        self.cache_dir = cache_dir
        self.cache_duration_minutes = cache_duration_minutes
        self.faiss_index_file = cache_dir / "jobs_index.faiss"
        self.jobs_data_file = cache_dir / "jobs_data.pkl"
        self.cache_metadata_file = cache_dir / "cache_metadata.pkl"

        self.index = None
        self.jobs_df = None
        self.last_updated = None
        self.total_jobs_count = 0

    def is_cache_valid(self) -> bool:
        if not self.cache_metadata_file.exists():
            return False
        try:
            with open(self.cache_metadata_file, "rb") as f:
                metadata = pickle.load(f)
            last_updated = metadata.get("last_updated")
            if not last_updated:
                return False
            time_diff = datetime.now() - last_updated
            return time_diff < timedelta(minutes=self.cache_duration_minutes)
        except Exception as e:
            # Log the specific error for debugging
            import logging
            logging.warning(f"Cache validation failed: {e}")
            return False
        
    def check_mongodb_changes(self, client, db_name: str, collection_name: str) -> bool:
        try:
            db = client[db_name]
            coll = db[collection_name]
            current_count = coll.count_documents({"status": "ACTIVE"})
            if self.cache_metadata_file.exists():
                with open(self.cache_metadata_file, "rb") as f:
                    metadata = pickle.load(f)
                    cached_count = metadata.get("total_jobs_count", 0)
                return current_count != cached_count
            return True
        except Exception as e:
            import logging
            logging.warning(f"MongoDB change check failed: {e}")
            return True
        
    def load_from_disk(self) -> bool:
        try:
            if not self.faiss_index_file.exists() or not self.jobs_data_file.exists():
                return False
            self.index = faiss.read_index(str(self.faiss_index_file))
            with open(self.jobs_data_file, "rb") as f:
                self.jobs_df = pickle.load(f)
            with open(self.cache_metadata_file, "rb") as f:
                metadata = pickle.load(f)
                self.last_updated = metadata.get("last_updated")
                self.total_jobs_count = metadata.get("total_jobs_count", 0)
            return True
        except Exception as e:
            import logging
            logging.warning(f"Failed to load cache from disk: {e}")
            return False

    def save_to_disk(self):
        try:
            faiss.write_index(self.index, str(self.faiss_index_file))
            with open(self.jobs_data_file, "wb") as f:
                pickle.dump(self.jobs_df, f)
            metadata = {
                "last_updated": self.last_updated,
                "total_jobs_count": self.total_jobs_count,
            }
            with open(self.cache_metadata_file, "wb") as f:
                pickle.dump(metadata, f)
        except Exception as e:
            import logging
            logging.error(f"Failed to save cache to disk: {e}")
            raise

    def build_from_mongodb(self, jobs_df: pd.DataFrame, model: SentenceTransformer):
        if jobs_df.empty:
            return

        # Create a copy to avoid modifying original
        jobs_copy = jobs_df.copy()
        jobs_copy["combined_text"] = jobs_copy.apply(build_job_text, axis=1)

        job_embeddings = model.encode(
            jobs_copy["combined_text"].tolist(),
            batch_size=8,
            convert_to_numpy=True,
            show_progress_bar=True,
        )
        faiss.normalize_L2(job_embeddings)

        dim = job_embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(job_embeddings)

        self.index = index
        self.jobs_df = jobs_df  # Store original dataframe
        self.last_updated = datetime.now()
        self.total_jobs_count = len(jobs_df)

        self.save_to_disk()

    def get_or_build(self, client, db_name: str, collection_name: str, 
                     jobs_df: pd.DataFrame, model: SentenceTransformer) -> Tuple[faiss.Index, pd.DataFrame]:
        if self.is_cache_valid():
            if self.index is None:
                if not self.load_from_disk():
                    self.build_from_mongodb(jobs_df, model)
            if self.check_mongodb_changes(client, db_name, collection_name):
                self.build_from_mongodb(jobs_df, model)
        else:
            self.build_from_mongodb(jobs_df, model)
        return self.index, self.jobs_df