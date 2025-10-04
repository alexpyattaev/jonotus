import os
import json
import logging
from datetime import datetime
from typing import Dict, Tuple
from config import QUEUE_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueueManager:
    """Manages queue tracking and cleanup to enforce the queue limit"""
    
    def __init__(self, max_queues: int = 1_000_000):
        """Initialize queue manager with optional queue limit and usage tracking"""
        self.max_queues = max_queues
        self.usage_file = os.path.join(QUEUE_DIR, "_queue_usage.json")
        self._load_usage()
        
    def _load_usage(self) -> None:
        """Load queue usage tracking data"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, "r") as f:
                    self.usage_data = json.load(f)
            else:
                self.usage_data = {}
        except Exception as e:
            logger.error(f"Failed to load usage data: {e}")
            self.usage_data = {}
    
    def _save_usage(self) -> None:
        """Save queue usage tracking data"""
        try:
            with open(self.usage_file, "w") as f:
                json.dump(self.usage_data, f)
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")
    
    def track_access(self, queue_id: str) -> None:
        """Record queue access"""
        now = datetime.now().isoformat()
        if queue_id not in self.usage_data:
            self.usage_data[queue_id] = {"access_count": 0, "last_access": now}
        self.usage_data[queue_id]["access_count"] += 1
        self.usage_data[queue_id]["last_access"] = now
        self._save_usage()
        logger.info(f"Tracked access for queue {queue_id}")
    
    def cleanup_if_needed(self) -> bool:
        """Check if cleanup is needed and perform it if necessary"""
        queue_files = [f for f in os.listdir(QUEUE_DIR)
                    if f.endswith(".json") and f != "_queue_usage.json"]
        current_count = len(queue_files)
        logger.info(f"Current queue count: {current_count}")
        
        if current_count > self.max_queues:
            return self._cleanup_queues()
        return False
    
    def _cleanup_queues(self) -> bool:
        """Remove least recently used queues until under limit"""
        try:
            # Get all queue files except usage data
            queue_files = [f for f in os.listdir(QUEUE_DIR)
                       if f.endswith(".json") and f != "_queue_usage.json"]
            
            if len(queue_files) <= self.max_queues:
                return False
                
            # Sort queues by usage (least used first)
            sorted_queues = []
            for queue_file in queue_files:
                queue_id = queue_file[:-5]  # Remove .json
                usage = self.usage_data.get(queue_id, {"access_count": 0, "last_access": "0"})
                sorted_queues.append((queue_id, usage))
                
            sorted_queues.sort(key=lambda x: (x[1]["access_count"], x[1]["last_access"]))
            
            # Remove queues until under limit
            queues_to_remove = sorted_queues[:len(queue_files) - self.max_queues]
            for queue_id, _ in queues_to_remove:
                try:
                    os.remove(os.path.join(QUEUE_DIR, f"{queue_id}.json"))
                    if queue_id in self.usage_data:
                        del self.usage_data[queue_id]
                except OSError as e:
                    logger.error(f"Failed to remove queue {queue_id}: {e}")
            
            self._save_usage()
            return True
            
        except Exception as e:
            logger.error(f"Queue cleanup failed: {e}")
            return False