import pytest
import os
import sys
import json
from datetime import datetime

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../app/services"))
)
from app.services.events import EventPublisher


class DummyRedis:
    def __init__(self):
        self.stream = []

    def xadd(self, stream_name, event):
        self.stream.append((stream_name, event))

    def xread(self, streams, count=10, block=1000):
        # Return last 'count' events
        return [("user_events", self.stream[-count:])]

    def ping(self):
        return True


@pytest.fixture(autouse=True)
def patch_redis(monkeypatch):
    dummy_redis = DummyRedis()
    monkeypatch.setattr(EventPublisher, "get_redis_client", lambda: dummy_redis)


def test_publish_user_registered():
    event = EventPublisher.publish_user_registered(
        user_id="testid", email="test@example.com", full_name="Test User"
    )
    assert event["event_type"] == "UserRegistered"
    assert event["user_id"] == "testid"
    assert event["email"] == "test@example.com"
    assert event["full_name"] == "Test User"
    assert "timestamp" in event


def test_publish_user_registered_no_fullname():
    event = EventPublisher.publish_user_registered(
        user_id="testid", email="test@example.com"
    )
    assert event["event_type"] == "UserRegistered"
    assert event["user_id"] == "testid"
    assert event["email"] == "test@example.com"
    assert "full_name" not in event or event["full_name"] == ""
    assert "timestamp" in event


def test_get_events():
    # Publish two events
    EventPublisher.publish_user_registered("id1", "a@example.com", "A")
    EventPublisher.publish_user_registered("id2", "b@example.com", "B")
    msgs = EventPublisher.get_events(count=2)
    assert isinstance(msgs, list)
    assert len(msgs) == 1 or len(msgs) == 2  # DummyRedis returns one stream with events
    # Check event content
    stream_name, events = msgs[0]
    assert stream_name == "user_events"
    assert len(events) >= 2
    for event in events:
        assert isinstance(event[1], dict)
        assert "event_type" in event[1]
        assert "user_id" in event[1]
        assert "email" in event[1]
