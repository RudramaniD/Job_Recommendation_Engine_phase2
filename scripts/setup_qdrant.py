from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
import os

def setup_qdrant():
    client = QdrantClient("localhost", port=6333)

    collection_name = "job_embeddings"

    try:
        client.create_collection(
            collection_name = collection_name,
            vectors_config = VectorParams(size=1024, distance = Distance.COSINE)
        )
        print(f"Collection '{collection_name}' created successfully")
    except Exception as e:
        print(f"Collection might already exist: {e}")

if __name__ == "__main__":
    setup_qdrant()