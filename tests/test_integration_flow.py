import pytest
import datetime
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_storage_classes import Queue

@pytest.fixture
def queue_json():
    queue = Queue(
        name="IntegrationTestQueue",
        opening_time=datetime.time(10, 0),
        closing_time=datetime.time(18, 0),
        max_slots=50
    )
    return queue.as_json()

def test_queue_roundtrip(queue_json):
    q = Queue.from_json(queue_json)
    assert isinstance(q, Queue)
    assert q.name == "IntegrationTestQueue"
    assert q.opening_time == datetime.time(10, 0)
    assert q.closing_time == datetime.time(18, 0)
    assert q.max_slots == 50
