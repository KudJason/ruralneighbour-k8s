import json
import asyncio
from typing import Dict, Any, cast, Iterable, Tuple
import os
import uuid
from ..db.base import SessionLocal
from ..crud.profile import ProfileCRUD
from ..schemas.profile import UserProfileCreate

try:
    import redis
except ImportError:
    redis = None


class EventConsumer:
    """Event consumer for handling UserRegistered and RatingCreated events"""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

    def get_redis_client(self):
        if redis is None:
            raise RuntimeError("redis-py not installed")
        return redis.Redis.from_url(self.redis_url)

    async def start_consuming(self):
        """Start consuming events from Redis streams (user_lifecycle, service_lifecycle)"""
        try:
            r = self.get_redis_client()
            print("[EVENT CONSUMER] Starting to consume events...")

            last_ids: Dict[bytes, bytes] = {
                b"user_lifecycle": b"0",
                b"service_lifecycle": b"0",
            }
            processed_event_ids = set()  # 幂等处理
            while True:
                try:
                    loop = asyncio.get_running_loop()
                    raw = await loop.run_in_executor(
                        None,
                        lambda: r.xread(cast(Any, last_ids), count=10, block=1000),  # type: ignore
                    )
                    messages = cast(Iterable[Tuple[bytes, Any]], raw)

                    for stream_name, stream_messages in messages:
                        name = stream_name.decode()
                        for message_id, fields in stream_messages:
                            event_data = {
                                k.decode(): v.decode() for k, v in fields.items()
                            }
                            event_id = event_data.get("event_id")
                            if event_id and event_id in processed_event_ids:
                                print(
                                    f"[EVENT CONSUMER] Duplicate event skipped: {event_id}"
                                )
                                continue
                            await self.process_event(name, event_data)
                            last_ids[stream_name] = message_id
                            if event_id:
                                processed_event_ids.add(event_id)

                except Exception as e:
                    print(f"[EVENT CONSUMER][ERROR] Error reading events: {e}")
                    await asyncio.sleep(5)

        except Exception as e:
            print(f"[EVENT CONSUMER][ERROR] Failed to start consumer: {e}")

    async def process_event(self, stream_name: str, event_data: Dict[str, str]):
        """Process individual events (standardized structure)"""
        try:
            event_type = event_data.get("event_type")
            event_id = event_data.get("event_id")
            print(
                f"[EVENT CONSUMER] Processing {event_type} ({event_id}) from {stream_name}"
            )

            if event_type == "UserRegistered":
                await self.handle_user_registered(event_data)
            elif event_type == "RatingCreated":
                await self.handle_rating_created(event_data)
            else:
                print(f"[EVENT CONSUMER] Unknown event type: {event_type}")

        except Exception as e:
            print(f"[EVENT CONSUMER][ERROR] Error processing event: {e}")

    async def handle_user_registered(self, event_data: Dict[str, str]):
        """Handle UserRegistered event by creating user profile"""
        try:
            user_id = event_data.get("user_id")
            if not user_id:
                print(f"[EVENT CONSUMER][ERROR] Missing user_id in event: {event_data}")
                return
            user_id = uuid.UUID(user_id)

            db = SessionLocal()
            try:
                existing_profile = ProfileCRUD.get_user_profile(db, user_id)
                if existing_profile:
                    print(f"[EVENT CONSUMER] Profile already exists for user {user_id}")
                    return

                profile_data = UserProfileCreate(user_id=user_id)
                new_profile = ProfileCRUD.create_user_profile(db, profile_data)

                print(
                    f"[EVENT CONSUMER] Created profile for user {user_id}: {new_profile.profile_id}"
                )

            finally:
                db.close()

        except Exception as e:
            print(f"[EVENT CONSUMER][ERROR] Error handling UserRegistered: {e}")

    async def handle_rating_created(self, event_data: Dict[str, str]):
        """Handle RatingCreated event by updating average rating"""
        try:
            rated_user_id = event_data.get("rated_user_id")
            rating_value = event_data.get("rating")
            if not rated_user_id or not rating_value:
                print(
                    f"[EVENT CONSUMER][ERROR] Missing rated_user_id or rating in event: {event_data}"
                )
                return
            rated_user_id = uuid.UUID(rated_user_id)
            rating_value = float(rating_value)

            db = SessionLocal()
            try:
                updated_profile = ProfileCRUD.update_rating(
                    db, rated_user_id, rating_value
                )
                if updated_profile:
                    print(
                        f"[EVENT CONSUMER] Updated rating for user {rated_user_id}: avg={updated_profile.average_rating}, total={updated_profile.total_ratings}"
                    )
                else:
                    print(
                        f"[EVENT CONSUMER] Profile not found for user {rated_user_id}"
                    )

            finally:
                db.close()

        except Exception as e:
            print(f"[EVENT CONSUMER][ERROR] Error handling RatingCreated: {e}")
