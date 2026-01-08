import logging
from typing import Dict, Any
from ..core.layer0_validation import validate_job_record

logger = logging.getLogger(__name__)

class EventHandler:
    def __init__(self, recommendation_engine):
        self.engine = recommendation_engine
        self.events_processed = 0
    
    def handle_insert(self, document: Dict[str, Any]) -> None:
        try:
            validated_job = validate_job_record(document)
            if validated_job is None:
                logger.debug(f"Skipped invalid job: {document.get('jobId')}")
                return
            
            if validated_job.get("status") == "ACTIVE":
                self.engine.add_new_job_to_vectordb(validated_job)
                logger.info(f"Added job to Qdrant: {validated_job.get('jobId')}")
            else:
                logger.debug(f"Skipped INACTIVE job: {validated_job.get('jobId')}")
            
            self.events_processed += 1
            
        except Exception as e:
            logger.error(f"Failed to handle insert: {e}")
            raise
    
    def handle_update(self, document_id: str, full_document: Dict[str, Any], 
                     update_description: Dict[str, Any]) -> None:
        try:
            if full_document is None:
                logger.warning(f"No full document for update: {document_id}")
                return
            
            validated_job = validate_job_record(full_document)
            if validated_job is None:
                logger.debug(f"Skipped invalid job update: {document_id}")
                return
            
            job_id = validated_job.get("jobId", str(document_id))
            new_status = validated_job.get("status")
            
            updated_fields = update_description.get("updatedFields", {})
            old_status = self._get_old_status(updated_fields, new_status)
            
            if old_status == "INACTIVE" and new_status == "ACTIVE":
                self.engine.add_new_job_to_vectordb(validated_job)
                logger.info(f"Job activated, added to Qdrant: {job_id}")
            
            elif old_status == "ACTIVE" and new_status == "INACTIVE":
                self.engine.vectordb.delete_job(job_id)
                logger.info(f"Job deactivated, removed from Qdrant: {job_id}")
            
            elif new_status == "ACTIVE":
                self.engine.update_job_in_vectordb(job_id, validated_job)
                logger.info(f"Updated job in Qdrant: {job_id}")
            
            else:
                logger.debug(f"Skipped INACTIVE job update: {job_id}")
            
            self.events_processed += 1
            
        except Exception as e:
            logger.error(f"Failed to handle update: {e}")
            raise
    
    def handle_delete(self, document_id: str) -> None:
        try:
            job_id = str(document_id)
            self.engine.vectordb.delete_job(job_id)
            logger.info(f"Deleted job from Qdrant: {job_id}")
            self.events_processed += 1
            
        except Exception as e:
            logger.error(f"Failed to handle delete: {e}")
            raise
    
    def handle_replace(self, document: Dict[str, Any]) -> None:
        try:
            validated_job = validate_job_record(document)
            if validated_job is None:
                logger.debug(f"Skipped invalid job replacement: {document.get('jobId')}")
                return
            
            job_id = validated_job.get("jobId")
            
            if validated_job.get("status") == "ACTIVE":
                self.engine.update_job_in_vectordb(job_id, validated_job)
                logger.info(f"Replaced job in Qdrant: {job_id}")
            else:
                self.engine.vectordb.delete_job(job_id)
                logger.info(f"Replaced with INACTIVE, removed from Qdrant: {job_id}")
            
            self.events_processed += 1
            
        except Exception as e:
            logger.error(f"Failed to handle replace: {e}")
            raise
    
    def _get_old_status(self, updated_fields: Dict[str, Any], new_status: str) -> str:
        if "status" in updated_fields:
            return "INACTIVE" if new_status == "ACTIVE" else "ACTIVE"
        return new_status
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "events_processed": self.events_processed
        }