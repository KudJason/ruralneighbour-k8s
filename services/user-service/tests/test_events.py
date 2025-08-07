import pytest
import os
import sys
import json
from datetime import datetime
import uuid


from app.services.event_consumer import EventConsumer
from app.services.events import EventPublisher


class DummyRedis:
    def __init__(self):
        self.streams = {
            "user_lifecycle": [],
            "service_lifecycle": [],
            "rating_events": [],
        }

    def xadd(self, stream_name, event):
        if stream_name not in self.streams:
            self.streams[stream_name] = []
        self.streams[stream_name].append(
            (f"msg-{len(self.streams[stream_name])}", event)
        )

    def xread(self, streams, count=10, block=1000):
        result = []
        for stream_name, start_id in streams.items():
            if stream_name in self.streams:
                events = (
                    self.streams[stream_name][-count:]
                    if self.streams[stream_name]
                    else []
                )
                if events:
                    result.append((stream_name.encode(), events))
        return result


def test_publish_profile_updated():
    """Test publishing ProfileUpdated event"""
    user_id = str(uuid.uuid4())
    profile_id = str(uuid.uuid4())
    update_type = "bio"
    event = EventPublisher.publish_profile_updated(user_id, profile_id, update_type)
    assert event["event_type"] == "ProfileUpdated"
    assert event["user_id"] == user_id
    assert event["profile_id"] == profile_id
    assert event["update_type"] == update_type
    assert "event_id" in event
    assert "timestamp" in event


def test_publish_mode_changed():
    """Test publishing ModeChanged event"""
    user_id = str(uuid.uuid4())
    event = EventPublisher.publish_mode_changed(user_id, "NIN", "LAH")
    assert event["event_type"] == "ModeChanged"
    assert event["user_id"] == user_id
    assert event["old_mode"] == "NIN"
    assert event["new_mode"] == "LAH"
    assert "event_id" in event
    assert "timestamp" in event

    def ping(self):
        return True


@pytest.fixture(autouse=True)
def patch_redis(monkeypatch):
    dummy_redis = DummyRedis()
    monkeypatch.setattr(EventConsumer, "get_redis_client", lambda self: dummy_redis)
    return dummy_redis


@pytest.mark.asyncio
async def test_handle_user_registered():
    """Test handling UserRegistered event"""
    consumer = EventConsumer()

    # Mock event data
    event_data = {
        "event_type": "UserRegistered",
        "user_id": str(uuid.uuid4()),
        "email": "test@example.com",
        "full_name": "Test User",
        "timestamp": datetime.utcnow().isoformat(),
    }

    # This would normally create a profile in the database
    # For testing, we just verify the event is processed without errors
    await consumer.handle_user_registered(event_data)


@pytest.mark.asyncio
async def test_handle_rating_created():
    """Test handling RatingCreated event"""
    consumer = EventConsumer()

    # Mock event data
    event_data = {
        "event_type": "RatingCreated",
        "rated_user_id": str(uuid.uuid4()),
        "rating": "4.5",
        "timestamp": datetime.utcnow().isoformat(),
    }

    # This would normally update user's rating in the database
    # For testing, we just verify the event is processed without errors
    await consumer.handle_rating_created(event_data)


@pytest.mark.asyncio
async def test_process_event():
    """Test processing events from Redis stream (standardized structure)"""
    consumer = EventConsumer()

    # Mock stream data for ProfileUpdated
    stream_name = "user_lifecycle"
    fields = {
        b"event_type": b"ProfileUpdated",
        b"event_id": str(uuid.uuid4()).encode(),
        b"user_id": str(uuid.uuid4()).encode(),
        b"profile_id": str(uuid.uuid4()).encode(),
        b"update_type": b"bio",
        b"timestamp": datetime.utcnow().isoformat().encode(),
    }
    event_data = {k.decode(): v.decode() for k, v in fields.items()}
    await consumer.process_event(stream_name, event_data)

    # Mock stream data for ModeChanged
    fields2 = {
        b"event_type": b"ModeChanged",
        b"event_id": str(uuid.uuid4()).encode(),
        b"user_id": str(uuid.uuid4()).encode(),
        b"old_mode": b"NIN",
        b"new_mode": b"LAH",
        b"timestamp": datetime.utcnow().isoformat().encode(),
    }
    event_data2 = {k.decode(): v.decode() for k, v in fields2.items()}
    await consumer.process_event(stream_name, event_data2)


def test_event_consumer_initialization():
    """Test EventConsumer initialization"""
    consumer = EventConsumer()
    assert consumer.redis_url == "redis://redis:6379/0"
