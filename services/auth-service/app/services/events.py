import json
from typing import Dict, Any, Optional
from datetime import datetime
import os

try:
    import redis
except ImportError:
    redis = None


from typing import Optional


class EventPublisher:
    """Event publisher using Redis Stream. Config from env, test可mock."""

    @staticmethod
    def get_redis_client():
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        if redis is None:
            raise RuntimeError("redis-py not installed")
        return redis.Redis.from_url(redis_url)

    @staticmethod
    def publish_event(stream: str, event_type: str, payload: dict) -> dict:
        """
        通用事件发布方法，自动生成 event_id、timestamp，标准化结构。
        """
        import uuid

        event = {
            "event_type": event_type,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
        }
        # payload 展开到 event
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
    def publish_user_registered(
        user_id: str,
        email: str,
        full_name: str = "",
        default_mode: Optional[str] = None,
    ):
        """
        发布用户注册事件到 user_lifecycle 流，结构标准化。
        """
        payload = {
            "user_id": user_id,
            "email": email,
            "full_name": full_name,
            "default_mode": default_mode,
        }
        # 移除 None 和空字符串字段
        payload = {k: v for k, v in payload.items() if v not in [None, ""]}
        return EventPublisher.publish_event("user_lifecycle", "UserRegistered", payload)

    @staticmethod
    def get_events(stream="user_lifecycle", count=10):
        """从 Redis Stream 拉取事件（仅演示）"""
        try:
            r = EventPublisher.get_redis_client()
            msgs = r.xread({stream: "0"}, count=count, block=1000)
            return msgs if msgs is not None else []
        except Exception as e:
            print(f"[EVENT][ERROR] Redis get failed: {e}")
            return []
