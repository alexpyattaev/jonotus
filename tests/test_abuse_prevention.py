import pytest
import datetime
import json
import sys
import os


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_storage_classes import Queue


@pytest.fixture
def fresh_queue():
    return Queue(
        name="TestQueue",
        opening_time=datetime.time(9, 0),
        closing_time=datetime.time(17, 0),
        max_slots=100
    )

def test_queue_serialization(fresh_queue):
    json_data = fresh_queue.as_json()
    assert isinstance(json_data, str)

def test_queue_deserialization(fresh_queue):
    json_data = fresh_queue.as_json()
    new_queue = Queue.from_json(json_data)
    assert new_queue.name == fresh_queue.name
    assert new_queue.opening_time == fresh_queue.opening_time
    assert new_queue.closing_time == fresh_queue.closing_time
    assert new_queue.max_slots == fresh_queue.max_slots
