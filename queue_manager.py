import os
import json
import logging
from datetime import datetime
from typing import Dict, Tuple
from config import QUEUE_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueueManager:
    MAX_QUEUES = 1_000_000  # 1 million queue limit
    
    def __init__(self):
        self.usage_file = os.path.join(QUEUE_DIR, '_queue_usage.json')
        self._load_usage()
        
    def _load_usage(self) -> None:
        """Load queue usage tracking data"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    self.usage_data = json.load(f)
            else:
                self.usage_data = {}
        except Exception as e:
            logger.error(f"Failed to load usage data: {e}")
            self.usage_data = {}
    
    def _save_usage(self) -> None:
        """Save queue usage tracking data"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f)
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")
    
    def track_access(self, queue_id: str) -> None:
        """Record queue access"""
        now = datetime.now().isoformat()
        if queue_id not in self.usage_data:
            self.usage_data[queue_id] = {'access_count': 0, 'last_access': now}
        self.usage_data[queue_id]['access_count'] += 1
        self.usage_data[queue_id]['last_access'] = now
        self._save_usage()
        logger.info(f"Tracked access for queue {queue_id}")
    
    def cleanup_if_needed(self) -> bool:
        """Remove least used queues if count exceeds limit"""
        current_count = len([f for f in os.listdir(QUEUE_DIR) 
                           if f.endswith('.json') and f != '_queue_usage.json'])
        
        logger.info(f"Current queue count: {current_count}")
        
        if current_count <= self.MAX_QUEUES:
            return False
        
        # Calculate how many queues to remove (include buffer to prevent frequent cleanups)
        to_remove = current_count - self.MAX_QUEUES + 100
        logger.info(f"Need to remove {to_remove} queues")
        
        # Sort queues by usage (access count and last access time)
        queue_usage = [(qid, data['access_count'], data['last_access']) 
                      for qid, data in self.usage_data.items()]
        queue_usage.sort(key=lambda x: (x[1], x[2]))  # Sort by access count, then last access
        
        # Remove least used queues
        removed = 0
        for queue_id, count, last_access in queue_usage[:to_remove]:
            try:
                queue_file = os.path.join(QUEUE_DIR, f"{queue_id}.json")
                if os.path.exists(queue_file):
                    os.remove(queue_file)
                    del self.usage_data[queue_id]
                    removed += 1
                    logger.info(f"Removed queue {queue_id} (access count: {count}, last access: {last_access})")
            except Exception as e:
                logger.error(f"Failed to remove queue {queue_id}: {e}")
        
        self._save_usage()
        logger.info(f"Cleanup completed. Removed {removed} queues")
        return True