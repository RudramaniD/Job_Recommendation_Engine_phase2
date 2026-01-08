import logging
import time
import signal
from typing import Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)

class ChangeStreamListener:
    def __init__(self, mongo_uri: str, db_name: str, collection_name: str, 
                 event_handler, resume_token_manager):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.event_handler = event_handler
        self.resume_token_manager = resume_token_manager
        self.running = False
        self.client: Optional[MongoClient] = None
    
    def start(self) -> None:
        self.running = True
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        
        logger.info("Starting MongoDB Change Stream Listener...")
        
        while self.running:
            try:
                self._watch_changes()
            except PyMongoError as e:
                logger.error(f"MongoDB error: {e}")
                if self.running:
                    logger.info("Reconnecting in 5 seconds...")
                    time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if self.running:
                    logger.info("Restarting in 5 seconds...")
                    time.sleep(5)
    
    def stop(self) -> None:
        logger.info("Stopping Change Stream Listener...")
        self.running = False
        if self.client:
            self.client.close()
    
    def _watch_changes(self) -> None:
        self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
        db = self.client[self.db_name]
        collection = db[self.collection_name]
        
        pipeline = [
            {
                "$match": {
                    "operationType": {"$in": ["insert", "update", "delete", "replace"]}
                }
            }
        ]
        
        resume_token = self.resume_token_manager.load_token()
        
        watch_options = {
            "full_document": "updateLookup",
            "max_await_time_ms": 1000
        }
        
        if resume_token:
            watch_options["resume_after"] = resume_token
            logger.info("Resuming from saved token")
        else:
            logger.info("Starting fresh watch (no resume token)")
        
        with collection.watch(pipeline, **watch_options) as change_stream:
            logger.info(f"Watching collection: {self.db_name}.{self.collection_name}")
            
            for change in change_stream:
                if not self.running:
                    break
                
                try:
                    self._handle_event(change)
                    self.resume_token_manager.save_token(
                        change["_id"],
                        self.event_handler.events_processed
                    )
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
                    continue
    
    def _handle_event(self, change: Dict[str, Any]) -> None:
        operation = change["operationType"]
        
        if operation == "insert":
            self.event_handler.handle_insert(change["fullDocument"])
        
        elif operation == "update":
            self.event_handler.handle_update(
                change["documentKey"]["_id"],
                change.get("fullDocument"),
                change.get("updateDescription", {})
            )
        
        elif operation == "delete":
            self.event_handler.handle_delete(change["documentKey"]["_id"])
        
        elif operation == "replace":
            self.event_handler.handle_replace(change["fullDocument"])
    
    def _handle_shutdown(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def get_stats(self) -> Dict[str, Any]:
        token_stats = self.resume_token_manager.get_stats()
        handler_stats = self.event_handler.get_stats()
        
        return {
            "status": "running" if self.running else "stopped",
            "collection": f"{self.db_name}.{self.collection_name}",
            **token_stats,
            **handler_stats
        }
