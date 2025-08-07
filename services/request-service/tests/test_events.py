import pytest
import uuid
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from app.services.events import EventPublisher
from app.services.event_consumer import EventConsumer


class TestEventPublisher:
    """Test event publishing functionality"""

    def test_publish_service_request_created(self, mock_redis):
        """Test publishing ServiceRequestCreated event"""
        request_id = str(uuid.uuid4())
        requester_id = str(uuid.uuid4())
        location = {"latitude": 40.7128, "longitude": -74.0060}

        # Publish event
        EventPublisher.publish_service_request_created(
            request_id=request_id,
            requester_id=requester_id,
            service_type="transportation",
            location=location,
            title="Need ride to airport",
            offered_amount=25.0,
        )

        # Verify event was published
        assert "service_lifecycle" in mock_redis.streams
        events = mock_redis.streams["service_lifecycle"]
        assert len(events) == 1

        event_id, event_data = events[0]
        assert event_data["event_type"] == "ServiceRequestCreated"

        payload = json.loads(event_data["data"])
        assert payload["request_id"] == request_id
        assert payload["requester_id"] == requester_id
        assert payload["service_type"] == "transportation"
        assert payload["location"] == location
        assert payload["title"] == "Need ride to airport"
        assert payload["offered_amount"] == 25.0

    def test_publish_service_request_created_without_amount(self, mock_redis):
        """Test publishing ServiceRequestCreated event without offered amount"""
        request_id = str(uuid.uuid4())
        requester_id = str(uuid.uuid4())
        location = {"latitude": 40.7128, "longitude": -74.0060}

        EventPublisher.publish_service_request_created(
            request_id=request_id,
            requester_id=requester_id,
            service_type="errands",
            location=location,
            title="Grocery shopping help",
            offered_amount=None,
        )

        events = mock_redis.streams["service_lifecycle"]
        event_data = events[0][1]
        payload = json.loads(event_data["data"])
        assert payload["offered_amount"] is None

    def test_publish_request_status_changed(self, mock_redis):
        """Test publishing request status change event"""
        request_id = str(uuid.uuid4())
        requester_id = str(uuid.uuid4())
        provider_id = str(uuid.uuid4())

        EventPublisher.publish_request_status_changed(
            request_id=request_id,
            old_status="pending",
            new_status="accepted",
            requester_id=requester_id,
            provider_id=provider_id,
        )

        events = mock_redis.streams["service_lifecycle"]
        event_data = events[0][1]
        assert event_data["event_type"] == "RequestStatusChanged"

        payload = json.loads(event_data["data"])
        assert payload["request_id"] == request_id
        assert payload["old_status"] == "pending"
        assert payload["new_status"] == "accepted"
        assert payload["requester_id"] == requester_id
        assert payload["provider_id"] == provider_id

    def test_publish_service_completed(self, mock_redis):
        """Test publishing ServiceCompleted event"""
        request_id = str(uuid.uuid4())
        assignment_id = str(uuid.uuid4())
        requester_id = str(uuid.uuid4())
        provider_id = str(uuid.uuid4())
        completion_time = datetime.now().isoformat()

        EventPublisher.publish_service_completed(
            request_id=request_id,
            assignment_id=assignment_id,
            requester_id=requester_id,
            provider_id=provider_id,
            completion_time=completion_time,
        )

        events = mock_redis.streams["service_lifecycle"]
        event_data = events[0][1]
        assert event_data["event_type"] == "ServiceCompleted"

        payload = json.loads(event_data["data"])
        assert payload["request_id"] == request_id
        assert payload["assignment_id"] == assignment_id
        assert payload["requester_id"] == requester_id
        assert payload["provider_id"] == provider_id
        assert payload["completion_time"] == completion_time

    def test_publish_rating_created(self, mock_redis):
        """Test publishing RatingCreated event"""
        rating_id = str(uuid.uuid4())
        assignment_id = str(uuid.uuid4())
        rater_id = str(uuid.uuid4())
        ratee_id = str(uuid.uuid4())

        EventPublisher.publish_rating_created(
            rating_id=rating_id,
            assignment_id=assignment_id,
            rater_id=rater_id,
            ratee_id=ratee_id,
            rating_score=5,
            is_provider_rating=True,
            review_text="Excellent service!",
        )

        events = mock_redis.streams["service_lifecycle"]
        event_data = events[0][1]
        assert event_data["event_type"] == "RatingCreated"

        payload = json.loads(event_data["data"])
        assert payload["rating_id"] == rating_id
        assert payload["assignment_id"] == assignment_id
        assert payload["rater_id"] == rater_id
        assert payload["ratee_id"] == ratee_id
        assert payload["rating_score"] == 5
        assert payload["is_provider_rating"] is True
        assert payload["review_text"] == "Excellent service!"

    def test_publish_payment_completed(self, mock_redis):
        """Test publishing PaymentCompleted event"""
        request_id = str(uuid.uuid4())
        assignment_id = str(uuid.uuid4())
        requester_id = str(uuid.uuid4())
        provider_id = str(uuid.uuid4())

        EventPublisher.publish_payment_completed(
            request_id=request_id,
            assignment_id=assignment_id,
            requester_id=requester_id,
            provider_id=provider_id,
            amount=25.0,
            transaction_id="txn_12345",
        )

        events = mock_redis.streams["payment_lifecycle"]
        event_data = events[0][1]
        assert event_data["event_type"] == "PaymentCompleted"

        payload = json.loads(event_data["data"])
        assert payload["request_id"] == request_id
        assert payload["assignment_id"] == assignment_id
        assert payload["requester_id"] == requester_id
        assert payload["provider_id"] == provider_id
        assert payload["amount"] == 25.0
        assert payload["transaction_id"] == "txn_12345"

    def test_redis_connection_error_handling(self, monkeypatch):
        """Test handling of Redis connection errors"""
        # Mock Redis to raise an exception
        mock_redis_error = Mock()
        mock_redis_error.xadd.side_effect = Exception("Redis connection error")

        monkeypatch.setattr(
            EventPublisher, "get_redis_client", lambda: mock_redis_error
        )

        # Should not raise exception, just log error
        try:
            EventPublisher.publish_service_request_created(
                request_id=str(uuid.uuid4()),
                requester_id=str(uuid.uuid4()),
                service_type="transportation",
                location={"latitude": 40.7128, "longitude": -74.0060},
                title="Test request",
            )
        except Exception:
            pytest.fail("EventPublisher should handle Redis errors gracefully")


class TestEventConsumer:
    """Test event consumer functionality"""

    def test_consume_user_status_changed(self, mock_redis):
        """Test consuming UserStatusChanged event"""
        consumer = EventConsumer()

        # Mock the user status change handler
        with patch.object(consumer, "handle_user_status_changed") as mock_handler:
            # Simulate event in Redis stream
            user_id = str(uuid.uuid4())
            event_data = {
                "event_type": "UserStatusChanged",
                "data": json.dumps(
                    {
                        "user_id": user_id,
                        "old_status": "active",
                        "new_status": "suspended",
                    }
                ),
            }

            # Add event to mock stream
            mock_redis.xadd("user_lifecycle", event_data)

            # Mock Redis client to return events
            mock_redis.xread = Mock(
                return_value=[
                    (
                        "user_lifecycle",
                        [
                            (
                                b"1234-0",
                                {
                                    b"event_type": b"UserStatusChanged",
                                    b"data": event_data["data"].encode(),
                                },
                            )
                        ],
                    )
                ]
            )

            # Process events
            consumer.redis = mock_redis
            consumer.process_events(max_events=1)

            # Verify handler was called
            mock_handler.assert_called_once()
            call_args = mock_handler.call_args[0][0]
            assert call_args["user_id"] == user_id
            assert call_args["old_status"] == "active"
            assert call_args["new_status"] == "suspended"

    def test_handle_user_status_changed_suspend(self, db_session, mock_redis):
        """Test handling user suspension - should cancel active requests"""
        from app.models.service_request import (
            ServiceRequest,
            ServiceRequestStatus,
            ServiceType,
        )
        from app.crud.crud_service_request import ServiceRequestCRUD

        consumer = EventConsumer()
        user_id = uuid.uuid4()

        # Create active request for user
        from app.schemas.service_request import ServiceRequestCreate

        request_data = ServiceRequestCreate(
            title="Test request",
            description="Test description",
            service_type=ServiceType.TRANSPORTATION,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            destination_latitude=40.7589,
            destination_longitude=-73.9851,
            offered_amount=25.0,
        )

        service_request = ServiceRequestCRUD.create_service_request(
            db_session, request_data, user_id
        )
        assert service_request.status == ServiceRequestStatus.PENDING

        # Handle user suspension
        event_data = {
            "user_id": str(user_id),
            "old_status": "active",
            "new_status": "suspended",
        }

        consumer.handle_user_status_changed(event_data, db=db_session)

        # Verify request was cancelled
        db_session.refresh(service_request)
        assert service_request.status == ServiceRequestStatus.CANCELLED

    def test_handle_user_status_changed_delete(self, db_session):
        """Test handling user deletion - should hard delete requests"""
        from app.models.service_request import (
            ServiceRequest,
            ServiceRequestStatus,
            ServiceType,
        )
        from app.crud.crud_service_request import ServiceRequestCRUD

        consumer = EventConsumer()
        user_id = uuid.uuid4()

        # Create request for user
        from app.schemas.service_request import ServiceRequestCreate

        request_data = ServiceRequestCreate(
            title="Test request",
            description="Test description",
            service_type=ServiceType.TRANSPORTATION,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            destination_latitude=40.7589,
            destination_longitude=-73.9851,
            offered_amount=25.0,
        )

        service_request = ServiceRequestCRUD.create_service_request(
            db_session, request_data, user_id
        )
        request_id = service_request.request_id

        # Handle user deletion
        event_data = {
            "user_id": str(user_id),
            "old_status": "active",
            "new_status": "deleted",
        }

        consumer.handle_user_status_changed(event_data, db=db_session)

        # Verify request was hard deleted
        deleted_request = ServiceRequestCRUD.get_service_request(db_session, request_id)
        assert deleted_request is None

    def test_invalid_event_handling(self, mock_redis):
        """Test handling of invalid/malformed events"""
        consumer = EventConsumer()

        # Mock Redis to return invalid event
        mock_redis.xread = Mock(
            return_value=[
                (
                    "user_lifecycle",
                    [
                        (
                            b"1234-0",
                            {b"event_type": b"InvalidEvent", b"data": b"invalid_json"},
                        )
                    ],
                )
            ]
        )

        consumer.redis = mock_redis

        # Should not raise exception for invalid events
        try:
            consumer.process_events(max_events=1)
        except Exception:
            pytest.fail("EventConsumer should handle invalid events gracefully")

    def test_redis_read_error_handling(self, monkeypatch):
        """Test handling of Redis read errors"""
        consumer = EventConsumer()

        # Mock Redis to raise error on read
        mock_redis_error = Mock()
        mock_redis_error.xread.side_effect = Exception("Redis read error")

        monkeypatch.setattr(consumer, "get_redis_client", lambda: mock_redis_error)

        # Should handle error gracefully
        try:
            consumer.process_events(max_events=1)
        except Exception:
            pytest.fail("EventConsumer should handle Redis read errors gracefully")

    def test_start_consuming_with_stop(self, mock_redis):
        """Test starting and stopping event consumption"""
        consumer = EventConsumer()
        consumer.redis = mock_redis

        # Mock Redis to return no events
        mock_redis.xread = Mock(return_value=[])

        # Start consuming in background and stop after short time
        import threading
        import time

        stop_event = threading.Event()

        def stop_after_delay():
            time.sleep(0.1)
            consumer.stop()

        # Start stop thread
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()

        # Start consuming (should stop when stop() is called)
        consumer.start_consuming()

        stop_thread.join()
        assert not consumer.running
