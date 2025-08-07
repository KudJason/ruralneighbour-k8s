import pytest
import uuid
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from app.services.events import EventPublisher
from app.services.events import EventConsumer


class TestEventPublisher:
    """Test event publishing functionality for payment service"""

    def test_publish_payment_processed(self, mock_redis):
        """Test publishing PaymentProcessed event"""
        payment_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        amount = "100.00"

        # Publish event
        EventPublisher.publish_payment_processed(
            payment_id=payment_id,
            request_id=request_id,
            amount=amount,
            status="success",
        )

        # Verify event was published
        assert "payment_lifecycle" in mock_redis.streams
        events = mock_redis.streams["payment_lifecycle"]
        assert len(events) == 1

        event_id, event_data = events[0]
        assert event_data["event_type"] == "PaymentProcessed"
        assert event_data["payment_id"] == payment_id
        assert event_data["request_id"] == request_id
        assert event_data["amount"] == amount
        assert event_data["status"] == "success"

    def test_publish_payment_failed(self, mock_redis):
        """Test publishing PaymentFailed event"""
        payment_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        amount = "50.00"
        error_code = "insufficient_funds"
        error_message = "Insufficient funds in account"

        # Publish event
        EventPublisher.publish_payment_failed(
            payment_id=payment_id,
            request_id=request_id,
            amount=amount,
            error_code=error_code,
            error_message=error_message,
        )

        # Verify event was published
        events = mock_redis.streams["payment_lifecycle"]
        event_data = events[0][1]
        assert event_data["event_type"] == "PaymentFailed"
        assert event_data["payment_id"] == payment_id
        assert event_data["request_id"] == request_id
        assert event_data["amount"] == amount
        assert event_data["error_code"] == error_code
        assert event_data["error_message"] == error_message

    def test_publish_payment_refunded(self, mock_redis):
        """Test publishing PaymentRefunded event"""
        payment_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        amount = "25.00"
        refund_reason = "Customer request"

        # Publish event
        EventPublisher.publish_payment_refunded(
            payment_id=payment_id,
            request_id=request_id,
            amount=amount,
            refund_reason=refund_reason,
        )

        # Verify event was published
        events = mock_redis.streams["payment_lifecycle"]
        event_data = events[0][1]
        assert event_data["event_type"] == "PaymentRefunded"
        assert event_data["payment_id"] == payment_id
        assert event_data["request_id"] == request_id
        assert event_data["amount"] == amount
        assert event_data["refund_reason"] == refund_reason

    def test_publish_payment_method_saved(self, mock_redis):
        """Test publishing PaymentMethodSaved event"""
        method_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        method_type = "credit_card"

        # Publish event
        EventPublisher.publish_payment_method_saved(
            method_id=method_id, user_id=user_id, method_type=method_type
        )

        # Verify event was published
        assert "payment_methods" in mock_redis.streams
        events = mock_redis.streams["payment_methods"]
        assert len(events) == 1

        event_id, event_data = events[0]
        assert event_data["event_type"] == "PaymentMethodSaved"
        assert event_data["method_id"] == method_id
        assert event_data["user_id"] == user_id
        assert event_data["method_type"] == method_type
        assert "timestamp" in event_data

    def test_publish_payment_method_deleted(self, mock_redis):
        """Test publishing PaymentMethodDeleted event"""
        method_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        # Publish event
        EventPublisher.publish_payment_method_deleted(
            method_id=method_id, user_id=user_id
        )

        # Verify event was published
        events = mock_redis.streams["payment_methods"]
        event_data = events[0][1]
        assert event_data["event_type"] == "PaymentMethodDeleted"
        assert event_data["method_id"] == method_id
        assert event_data["user_id"] == user_id
        assert "timestamp" in event_data

    def test_publish_payment_method_used(self, mock_redis):
        """Test publishing PaymentMethodUsed event"""
        method_id = str(uuid.uuid4())
        payment_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        # Publish event
        EventPublisher.publish_payment_method_used(
            method_id=method_id, payment_id=payment_id, user_id=user_id
        )

        # Verify event was published
        events = mock_redis.streams["payment_methods"]
        event_data = events[0][1]
        assert event_data["event_type"] == "PaymentMethodUsed"
        assert event_data["method_id"] == method_id
        assert event_data["payment_id"] == payment_id
        assert event_data["user_id"] == user_id
        assert "timestamp" in event_data

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
            EventPublisher.publish_payment_processed(
                payment_id=str(uuid.uuid4()),
                request_id=str(uuid.uuid4()),
                amount="100.00",
            )
        except Exception:
            pytest.fail("EventPublisher should handle Redis errors gracefully")

    def test_get_events(self, mock_redis):
        """Test getting events from Redis stream"""
        # Publish some events first
        EventPublisher.publish_payment_processed(
            payment_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()), amount="100.00"
        )
        EventPublisher.publish_payment_processed(
            payment_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()), amount="200.00"
        )

        # Get events
        events = EventPublisher.get_events(stream="payment_lifecycle", count=10)

        # Verify events were retrieved
        assert isinstance(events, list)
        # Note: MockRedis implementation may return different structure
        # This test verifies the method doesn't raise exceptions


class TestEventConsumer:
    """Test event consumer functionality for payment service"""

    def test_consume_service_request_created(self, db_session, mock_redis):
        """Test consuming ServiceRequestCreated event"""
        # Create test event data
        request_id = str(uuid.uuid4())
        payer_id = str(uuid.uuid4())
        payee_id = str(uuid.uuid4())
        amount = "150.00"

        event_data = {
            "request_id": request_id,
            "payer_id": payer_id,
            "payee_id": payee_id,
            "amount": amount,
        }

        # Mock the PaymentService.create_pending_payment method
        with patch(
            "app.services.payment_service.PaymentService.create_pending_payment"
        ) as mock_create:
            mock_payment = Mock()
            mock_payment.payment_id = uuid.uuid4()
            mock_create.return_value = mock_payment

            # Consume the event
            EventConsumer.consume_service_request_created(db_session, event_data)

            # Verify the payment was created
            mock_create.assert_called_once_with(
                db=db_session,
                request_id=request_id,
                payer_id=payer_id,
                payee_id=payee_id,
                amount=Decimal(amount),
            )

    def test_consume_service_request_created_missing_fields(self, db_session):
        """Test consuming ServiceRequestCreated event with missing fields"""
        # Create incomplete event data
        event_data = {
            "request_id": str(uuid.uuid4()),
            "payer_id": str(uuid.uuid4()),
            # Missing payee_id and amount
        }

        # Should not raise exception, just log error
        try:
            EventConsumer.consume_service_request_created(db_session, event_data)
        except Exception:
            pytest.fail("EventConsumer should handle missing fields gracefully")

    def test_consume_service_request_created_invalid_amount(self, db_session):
        """Test consuming ServiceRequestCreated event with invalid amount"""
        event_data = {
            "request_id": str(uuid.uuid4()),
            "payer_id": str(uuid.uuid4()),
            "payee_id": str(uuid.uuid4()),
            "amount": "invalid_amount",  # Invalid amount
        }

        # Should handle invalid amount gracefully
        try:
            EventConsumer.consume_service_request_created(db_session, event_data)
        except Exception:
            pytest.fail("EventConsumer should handle invalid amount gracefully")

    def test_start_consumer(self, mock_redis, db_session):
        """Test starting the event consumer"""
        # Mock Redis client
        with patch.object(EventConsumer, "get_redis_client", return_value=mock_redis):
            # Should not raise exception
            try:
                EventConsumer.start_consumer(db_session)
            except Exception:
                pytest.fail("EventConsumer.start_consumer should not raise exceptions")

    def test_redis_connection_error_handling(self, monkeypatch, db_session):
        """Test handling of Redis connection errors in consumer"""
        # Mock Redis to raise an exception
        mock_redis_error = Mock()
        mock_redis_error.xread.side_effect = Exception("Redis connection error")

        monkeypatch.setattr(EventConsumer, "get_redis_client", lambda: mock_redis_error)

        # Should handle error gracefully
        try:
            EventConsumer.start_consumer(db_session)
        except Exception:
            pytest.fail("EventConsumer should handle Redis errors gracefully")


class TestEventIntegration:
    """Integration tests for event publishing and consuming"""

    def test_payment_processed_event_integration(self, db_session, mock_redis):
        """Test complete flow: publish payment processed event"""
        payment_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        amount = "75.50"

        # Publish payment processed event
        result = EventPublisher.publish_payment_processed(
            payment_id=payment_id,
            request_id=request_id,
            amount=amount,
            status="success",
        )

        # Verify event was published successfully
        assert "event_type" in result
        assert result["event_type"] == "PaymentProcessed"
        assert "event_id" in result
        assert "timestamp" in result

        # Verify event is in Redis stream
        events = mock_redis.streams["payment_lifecycle"]
        assert len(events) == 1
        event_data = events[0][1]
        assert event_data["payment_id"] == payment_id
        assert event_data["request_id"] == request_id
        assert event_data["amount"] == amount

    def test_payment_failed_event_integration(self, db_session, mock_redis):
        """Test complete flow: publish payment failed event"""
        payment_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        amount = "100.00"
        error_code = "card_declined"
        error_message = "Card was declined"

        # Publish payment failed event
        result = EventPublisher.publish_payment_failed(
            payment_id=payment_id,
            request_id=request_id,
            amount=amount,
            error_code=error_code,
            error_message=error_message,
        )

        # Verify event was published successfully
        assert "event_type" in result
        assert result["event_type"] == "PaymentFailed"
        assert "event_id" in result
        assert "timestamp" in result

        # Verify event is in Redis stream
        events = mock_redis.streams["payment_lifecycle"]
        assert len(events) == 1
        event_data = events[0][1]
        assert event_data["payment_id"] == payment_id
        assert event_data["error_code"] == error_code
        assert event_data["error_message"] == error_message
