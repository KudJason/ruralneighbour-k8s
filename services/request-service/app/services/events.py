import redis
import json
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
from app.core.config import REDIS_URL


class EventPublisher:
    """
    Publishes events to Redis streams for other services to consume.
    Based on the PRD requirements for event-driven architecture.
    """

    @staticmethod
    def get_redis_client():
        """Get Redis client connection"""
        return redis.from_url(REDIS_URL)

    @staticmethod
    def _publish_event(stream_name: str, event_data: Dict[str, Any]) -> str:
        """
        Internal method to publish events to Redis stream

        Args:
            stream_name: The Redis stream name
            event_data: The event payload

        Returns:
            Event ID from Redis
        """
        try:
            redis_client = EventPublisher.get_redis_client()

            # Ensure all values are strings for Redis
            redis_data = {}
            for key, value in event_data.items():
                if isinstance(value, (dict, list)):
                    redis_data[key] = json.dumps(value)
                else:
                    redis_data[key] = str(value)

            # Add to Redis stream
            event_id = redis_client.xadd(stream_name, redis_data)
            redis_client.close()

            return event_id.decode() if isinstance(event_id, bytes) else str(event_id)
        except Exception as e:
            print(f"Failed to publish event to {stream_name}: {e}")
            # Don't re-raise the exception, just log it
            return None

    @staticmethod
    def publish_service_request_created(
        request_id: str,
        requester_id: str,
        service_type: str,
        location: Dict[str, float],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Publish ServiceRequestCreated event

        Args:
            request_id: UUID of the service request
            requester_id: UUID of the requester
            service_type: Type of service requested
            location: Geographic coordinates {"latitude": float, "longitude": float}
        """
        payload = {
            "request_id": request_id,
            "requester_id": requester_id,
            "service_type": service_type,
            "location": location,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs,
        }

        event_data = {
            "event_type": "ServiceRequestCreated",
            "event_id": str(uuid.uuid4()),
            "data": json.dumps(payload),
        }

        EventPublisher._publish_event("service_lifecycle", event_data)
        return event_data

    @staticmethod
    def publish_service_completed(
        request_id: str,
        assignment_id: str,
        requester_id: str,
        provider_id: str,
        completion_time: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Publish ServiceCompleted event

        Args:
            request_id: UUID of the service request
            assignment_id: UUID of the service assignment
            requester_id: UUID of the requester
            provider_id: UUID of the provider
            completion_time: ISO timestamp of completion
        """
        if completion_time is None:
            completion_time = datetime.utcnow().isoformat()

        payload = {
            "request_id": request_id,
            "assignment_id": assignment_id,
            "requester_id": requester_id,
            "provider_id": provider_id,
            "completion_time": completion_time,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs,
        }

        event_data = {
            "event_type": "ServiceCompleted",
            "event_id": str(uuid.uuid4()),
            "data": json.dumps(payload),
        }

        EventPublisher._publish_event("service_lifecycle", event_data)
        return event_data

    @staticmethod
    def publish_rating_created(
        rating_id: str,
        assignment_id: str,
        rater_id: str,
        ratee_id: str,
        rating_score: int,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Publish RatingCreated event

        Args:
            rating_id: UUID of the rating
            assignment_id: UUID of the service assignment
            rater_id: UUID of the user giving the rating
            ratee_id: UUID of the user receiving the rating
            rating_score: Rating score (1-5)
        """
        payload = {
            "rating_id": rating_id,
            "assignment_id": assignment_id,
            "rater_id": rater_id,
            "ratee_id": ratee_id,
            "rating_score": rating_score,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs,
        }

        event_data = {
            "event_type": "RatingCreated",
            "event_id": str(uuid.uuid4()),
            "data": json.dumps(payload),
        }

        EventPublisher._publish_event("service_lifecycle", event_data)
        return event_data

    @staticmethod
    def publish_request_status_changed(
        request_id: str,
        old_status: str,
        new_status: str,
        requester_id: str,
        provider_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Publish RequestStatusChanged event

        Args:
            request_id: UUID of the service request
            old_status: Previous status
            new_status: New status
            requester_id: UUID of the requester
            provider_id: UUID of the provider (if applicable)
        """
        payload = {
            "request_id": request_id,
            "old_status": old_status,
            "new_status": new_status,
            "requester_id": requester_id,
            "provider_id": provider_id,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs,
        }

        event_data = {
            "event_type": "RequestStatusChanged",
            "event_id": str(uuid.uuid4()),
            "data": json.dumps(payload),
        }

        EventPublisher._publish_event("service_lifecycle", event_data)
        return event_data

    @staticmethod
    def publish_payment_completed(
        request_id: str,
        requester_id: str,
        amount: float,
        assignment_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Publish PaymentCompleted event

        Args:
            request_id: UUID of the service request
            payment_id: UUID of the payment
            requester_id: UUID of the requester
            amount: Payment amount
        """
        payload = {
            "request_id": request_id,
            "requester_id": requester_id,
            "amount": amount,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs,
        }

        if assignment_id:
            payload["assignment_id"] = assignment_id
        if provider_id:
            payload["provider_id"] = provider_id

        event_data = {
            "event_type": "PaymentCompleted",
            "event_id": str(uuid.uuid4()),
            "data": json.dumps(payload),
        }

        EventPublisher._publish_event("payment_lifecycle", event_data)
        return event_data
