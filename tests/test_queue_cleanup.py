import unittest
import os
import json
import time
import sys

# Add root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from queue_manager import QueueManager
from config import QUEUE_DIR

class TestQueueCleanup(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        os.makedirs(QUEUE_DIR, exist_ok=True)
        # Clean any existing test files
        self.cleanup_test_files()
        # Create queue manager with small queue limit for testing
        self.queue_manager = QueueManager(max_queues=2)  # Only allow 2 queues for testing

    def tearDown(self):
        """Clean up after each test"""
        self.cleanup_test_files()

    def cleanup_test_files(self):
        """Helper method to remove test files"""
        if os.path.exists(QUEUE_DIR):
            # First remove usage data
            try:
                os.remove(os.path.join(QUEUE_DIR, '_queue_usage.json'))
            except OSError:
                pass
            # Then remove test queue files
            for file in os.listdir(QUEUE_DIR):
                if file.startswith('test_'):
                    try:
                        os.remove(os.path.join(QUEUE_DIR, file))
                    except OSError:
                        pass  # Ignore errors during cleanup

    def create_test_queue(self, queue_id, name="Test Queue"):
        """Helper method to create a test queue file"""
        file_path = os.path.join(QUEUE_DIR, f"{queue_id}.json")
        queue_data = {
            "name": name,
            "opening_time": "09:00",
            "closing_time": "17:00",
            "max_slots": 100
        }
        with open(file_path, 'w') as f:
            json.dump(queue_data, f)
        return file_path

    def test_queue_limit_enforcement(self):
        """Test that the system enforces the queue limit"""
        # Create a few test queues (just over the limit)
        test_queue_count = 3  # One more than our limit of 2
        for i in range(test_queue_count):
            queue_id = f"test_queue_{i}"
            self.create_test_queue(queue_id)
            
        # Verify initial count
        queue_count = len([f for f in os.listdir(QUEUE_DIR) if f.endswith('.json')])
        self.assertEqual(queue_count, test_queue_count)
        
        # Track accesses to make queue_0 and queue_1 most used
        self.queue_manager.track_access("test_queue_0")  # Used most
        self.queue_manager.track_access("test_queue_0")  # Second access
        self.queue_manager.track_access("test_queue_1")  # Used second most
        
        # Trigger cleanup
        self.queue_manager.cleanup_if_needed()
        
        # Verify most accessed queues (0 and 1) are kept while queue_2 is removed
        self.assertTrue(os.path.exists(os.path.join(QUEUE_DIR, "test_queue_0.json")))
        self.assertTrue(os.path.exists(os.path.join(QUEUE_DIR, "test_queue_1.json")))
        self.assertFalse(os.path.exists(os.path.join(QUEUE_DIR, "test_queue_2.json")))

    def test_least_used_queue_removal(self):
        """Test that least used queues are removed first"""
        # Create test queues
        queue_ids = ["test_frequent", "test_rare", "test_never"]
        for queue_id in queue_ids:
            self.create_test_queue(queue_id)

        # Simulate different usage patterns
        for _ in range(5):
            self.queue_manager.track_access("test_frequent")
        self.queue_manager.track_access("test_rare")
        # test_never is never accessed

        # Lower MAX_QUEUES temporarily to force cleanup
        original_max = self.queue_manager.max_queues
        self.queue_manager.max_queues = 1  # Only keep one queue
        
        # Force cleanup
        self.queue_manager._cleanup_queues()
        
        # Restore MAX_QUEUES
        self.queue_manager.max_queues = original_max

        # Verify results
        self.assertTrue(os.path.exists(os.path.join(QUEUE_DIR, "test_frequent.json")))
        self.assertFalse(os.path.exists(os.path.join(QUEUE_DIR, "test_never.json")))

    def test_usage_tracking_accuracy(self):
        """Test that queue usage is tracked accurately"""
        queue_id = "test_tracking"
        self.create_test_queue(queue_id)

        # Track multiple accesses
        access_count = 3
        for _ in range(access_count):
            self.queue_manager.track_access(queue_id)
            time.sleep(0.1)  # Small delay to ensure different timestamps

        # Verify the usage data
        usage_file = os.path.join(QUEUE_DIR, "_queue_usage.json")
        self.assertTrue(os.path.exists(usage_file))
        
        with open(usage_file, 'r') as f:
            usage_data = json.load(f)
        
        self.assertIn(queue_id, usage_data)
        self.assertEqual(usage_data[queue_id]["access_count"], access_count)

if __name__ == '__main__':
    unittest.main()