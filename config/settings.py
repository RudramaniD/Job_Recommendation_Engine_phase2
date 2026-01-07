import os
from pathlib import Path

# Use environment variable for MongoDB URI, fallback to default for development
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://skillorbit_qa_user:KekCGbwCRMDvN8l4@cluster0.euwijto.mongodb.net/skill_orbit_qa?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = "skill_orbit_qa"
JOBS_COLLECTION = "jobs"

EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"

CACHE_DIR = Path("./vector_cache")
CACHE_DURATION_MINUTES = 2
FAISS_INDEX_FILE = CACHE_DIR / "jobs_index.faiss"
JOBS_DATA_FILE = CACHE_DIR / "jobs_data.pkl"
CACHE_METADATA_FILE = CACHE_DIR / "cache_metadata.pkl"

MAX_SKILLS_COUNT = 50
MAX_TEXT_LENGTH = 1000
DEFAULT_EXPERIENCE_YEARS = 0

CACHE_DIR.mkdir(exist_ok=True)