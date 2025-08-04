import pytest
import datetime
import json
import sys
import os


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_storage_classes import Queue

def test_queue_creation():
    q = Queue(
        name="TestQueue",
        opening_time=datetime.time(9, 0),
        closing_time=datetime.time(17, 0),
        max_slots=10
    )
    assert q.name == "TestQueue"
    assert q.opening_time == datetime.time(9, 0)
    assert q.closing_time == datetime.time(17, 0)
    assert q.max_slots == 10

def test_queue_serialization():
    q = Queue(
        name="TestQueue",
        opening_time=datetime.time(8, 30),
        closing_time=datetime.time(16, 45),
        max_slots=15
    )
    json_data = q.as_json()
    assert isinstance(json_data, str)
    parsed = json.loads(json_data)
    assert parsed["name"] == "TestQueue"
    assert parsed["opening_time"] == "08:30:00"
    assert parsed["closing_time"] == "16:45:00"
    assert parsed["max_slots"] == 15

def test_queue_deserialization():
    json_input = '{"name": "DemoQueue", "opening_time": "07:00:00", "closing_time": "18:00:00", "max_slots": 25}'
    q = Queue.from_json(json_input)
    assert isinstance(q, Queue)
    assert q.name == "DemoQueue"
    assert q.opening_time == datetime.time(7, 0)
    assert q.closing_time == datetime.time(18, 0)
    assert q.max_slots == 25
