import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ResumeTokenManager:
    def __init__(self, token_file_path: Path):
        self.token_file_path = token_file_path
        self.token_file_path.parent.mkdir(parents=True, exist_ok=True)

    def save_token(self, token: Dict[str, Any], events_processed: int = 0) -> None:
        try:
            data = {
                "resume_token": token,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "events_processed": events_processed
            }

            temp_file = self.token_file_path.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)

            temp_file.replace(self.token_file_path)
            logger.debug(f"Resume token saved: {events_processed} events processed")

        except Exception as e:
            logger.error(f"Failed to save resume token: {e}")
            raise

    def load_token(self) -> Optional[Dict[str, Any]]:
        try:
            if not self.token_file_path.exists():
                logger.info("No resume token found, starting from beginning")
                return None

            with open(self.token_file_path, 'r') as f:
                data = json.load(f)

            logger.info(f"Resume token loaded: {data.get('events_processed', 0)} events processed")
            return data.get("resume_token")

        except json.JSONDecodeError as e:
            logger.error(f"Corrupted resume token file: {e}")
            return None
        except Exception as e:
            logger.info(f"Failed to load resume token: {e}")
            return None

    def clear_token(self) -> None:
        try:
            if self.token_file_path.exists():
                self.token_file_path.unlink()
                logger.info("Resume token cleared")
        except Exception as e:
            logger.error(f"Failed to clear resume token: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        try:
            if not self.token_file_path.exists():
                return {"status": "no_token", "events_processed": 0}
            
            with open(self.token_file_path, 'r') as f:
                data = json.load(f)
            
            return {
                "status": "active",
                "last_updated": data.get("last_updated"),
                "events_processed": data.get("events_processed", 0)
            }
        except Exception:
            return {"status": "error", "events_processed": 0}
