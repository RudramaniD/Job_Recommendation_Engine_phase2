import sys
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.sync_service_db.change_stream_listener import ChangeStreamListener
from src.sync_service_db.event_handler import EventHandler
from src.sync_service_db.resume_token_manager import ResumeTokenManager
from src.engine.qdrant_recommendation_engine import QdrantRecommendationEngine
from config.settings import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("="*60)
    logger.info("MongoDB Change Stream Sync Service")
    logger.info("="*60)
    
    config = {
        "MONGO_URI": MONGO_URI,
        "DB_NAME": DB_NAME,
        "JOBS_COLLECTION": JOBS_COLLECTION,
        "EMBEDDING_MODEL": EMBEDDING_MODEL,
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": 6333,
        "QDRANT_COLLECTION": "job_embeddings",
    }
    
    logger.info("Initializing recommendation engine...")
    engine = QdrantRecommendationEngine(config)
    
    logger.info("Initializing resume token manager...")
    resume_token_path = Path(".sync_data/resume_token.json")
    token_manager = ResumeTokenManager(resume_token_path)
    
    logger.info("Initializing event handler...")
    event_handler = EventHandler(engine)
    
    logger.info("Initializing change stream listener...")
    listener = ChangeStreamListener(
        mongo_uri=MONGO_URI,
        db_name=DB_NAME,
        collection_name=JOBS_COLLECTION,
        event_handler=event_handler,
        resume_token_manager=token_manager
    )
    
    logger.info("Starting sync service...")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*60)
    
    try:
        listener.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        listener.stop()
        logger.info("Sync service stopped")

if __name__ == "__main__":
    main()
