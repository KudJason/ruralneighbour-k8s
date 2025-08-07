import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import redis
except ImportError:
    redis = None


class EventPublisher:
    """User Service event publisher for ProfileUpdated and ModeChanged"""

    @staticmethod
    def get_redis_client():
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        if redis is None:
            raise RuntimeError("redis-py not installed")
        return redis.Redis.from_url(redis_url)

    @staticmethod
    def publish_event(
        stream: str, event_type: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        event = {
            "event_type": event_type,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
        }
        for k, v in payload.items():
            if v is not None:
                event[k] = str(v)
        try:
            r = EventPublisher.get_redis_client()
            r.xadd(stream, {k: v for k, v in event.items()})
            print(f"[EVENT][PUBLISH] {event_type} -> {stream}: {json.dumps(event)}")
            return event
        except Exception as e:
            print(f"[EVENT][ERROR] Redis publish failed: {e}")
            return {"error": str(e), **event}

    @staticmethod
    def publish_profile_updated(user_id: str, profile_id: str, update_type: str):
        payload = {
            "user_id": user_id,
            "profile_id": profile_id,
            "update_type": update_type,
        }
        return EventPublisher.publish_event("user_lifecycle", "ProfileUpdated", payload)

    @staticmethod
    def publish_mode_changed(user_id: str, old_mode: str, new_mode: str):
        payload = {
            "user_id": user_id,
            "old_mode": old_mode,
            "new_mode": new_mode,
        }
        return EventPublisher.publish_event("user_lifecycle", "ModeChanged", payload)
