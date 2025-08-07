import pytest
from app.services.event_service import EventService


class TestEventService:
    """Unit tests for EventService"""

    @pytest.fixture
    def user_registered_event_data(self):
        """Sample UserRegistered event data"""
        return {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "name": "Test User",
        }

    @pytest.fixture
    def profile_updated_event_data(self):
        """Sample ProfileUpdated event data"""
        return {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
        }

    @pytest.fixture
    def mode_changed_event_data(self):
        """Sample ModeChanged event data"""
        return {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "new_mode": "LAH",
        }

    @pytest.fixture
    def service_request_created_event_data(self):
        """Sample ServiceRequestCreated event data"""
        return {
            "requester_id": "550e8400-e29b-41d4-a716-446655440000",
            "request_id": "550e8400-e29b-41d4-a716-446655440001",
            "service_type": "cleaning",
        }

    @pytest.fixture
    def service_completed_event_data(self):
        """Sample ServiceCompleted event data"""
        return {
            "requester_id": "550e8400-e29b-41d4-a716-446655440000",
            "provider_id": "550e8400-e29b-41d4-a716-446655440001",
            "request_id": "550e8400-e29b-41d4-a716-446655440002",
        }

    @pytest.fixture
    def payment_processed_event_data(self):
        """Sample PaymentProcessed event data"""
        return {
            "payer_id": "550e8400-e29b-41d4-a716-446655440000",
            "payee_id": "550e8400-e29b-41d4-a716-446655440001",
            "amount": 100.00,
        }

    @pytest.fixture
    def payment_failed_event_data(self):
        """Sample PaymentFailed event data"""
        return {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "amount": 100.00,
        }

    @pytest.fixture
    def dispute_opened_event_data(self):
        """Sample DisputeOpened event data"""
        return {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "dispute_id": "550e8400-e29b-41d4-a716-446655440001",
        }

    @pytest.fixture
    def safety_report_filed_event_data(self):
        """Sample SafetyReportFiled event data"""
        return {
            "reporter_id": "550e8400-e29b-41d4-a716-446655440000",
            "report_id": "550e8400-e29b-41d4-a716-446655440001",
        }

    def test_handle_user_registered(self, db_session, user_registered_event_data):
        """Test handling UserRegistered event"""
        notification_id = EventService.handle_user_registered(
            db_session, user_registered_event_data
        )

        assert notification_id is not None

        # Verify notification was created
        from app.services.notification_service import NotificationService

        notification = NotificationService.get_notification(db_session, notification_id)
        assert notification is not None
        assert notification.title == "Welcome to Our Platform!"

    def test_handle_profile_updated(self, db_session, profile_updated_event_data):
        """Test handling ProfileUpdated event"""
        notification_id = EventService.handle_profile_updated(
            db_session, profile_updated_event_data
        )

        assert notification_id is not None

        # Verify notification was created
        from app.services.notification_service import NotificationService

        notification = NotificationService.get_notification(db_session, notification_id)
        assert notification is not None
        assert notification.title == "Profile Updated"

    def test_handle_mode_changed(self, db_session, mode_changed_event_data):
        """Test handling ModeChanged event"""
        notification_id = EventService.handle_mode_changed(
            db_session, mode_changed_event_data
        )

        assert notification_id is not None

        # Verify notification was created
        from app.services.notification_service import NotificationService

        notification = NotificationService.get_notification(db_session, notification_id)
        assert notification is not None
        assert notification.title == "Role Changed"

    def test_handle_service_request_created(
        self, db_session, service_request_created_event_data
    ):
        """Test handling ServiceRequestCreated event"""
        notification_id = EventService.handle_service_request_created(
            db_session, service_request_created_event_data
        )

        assert notification_id is not None

        # Verify notification was created
        from app.services.notification_service import NotificationService

        notification = NotificationService.get_notification(db_session, notification_id)
        assert notification is not None
        assert notification.title == "Service Request Created"

    def test_handle_service_completed(self, db_session, service_completed_event_data):
        """Test handling ServiceCompleted event"""
        notification_id = EventService.handle_service_completed(
            db_session, service_completed_event_data
        )

        assert notification_id is not None

        # Verify notifications were created for both requester and provider
        from app.services.notification_service import NotificationService

        requester_notifications = NotificationService.get_user_notifications(
            db_session, service_completed_event_data["requester_id"]
        )
        provider_notifications = NotificationService.get_user_notifications(
            db_session, service_completed_event_data["provider_id"]
        )

        assert requester_notifications.total_count == 1
        assert provider_notifications.total_count == 1

    def test_handle_payment_processed(self, db_session, payment_processed_event_data):
        """Test handling PaymentProcessed event"""
        notification_id = EventService.handle_payment_processed(
            db_session, payment_processed_event_data
        )

        assert notification_id is not None

        # Verify notifications were created for both payer and payee
        from app.services.notification_service import NotificationService

        payer_notifications = NotificationService.get_user_notifications(
            db_session, payment_processed_event_data["payer_id"]
        )
        payee_notifications = NotificationService.get_user_notifications(
            db_session, payment_processed_event_data["payee_id"]
        )

        assert payer_notifications.total_count == 1
        assert payee_notifications.total_count == 1

    def test_handle_payment_failed(self, db_session, payment_failed_event_data):
        """Test handling PaymentFailed event"""
        notification_id = EventService.handle_payment_failed(
            db_session, payment_failed_event_data
        )

        assert notification_id is not None

        # Verify notification was created
        from app.services.notification_service import NotificationService

        notification = NotificationService.get_notification(db_session, notification_id)
        assert notification is not None
        assert notification.title == "Payment Failed"

    def test_handle_dispute_opened(self, db_session, dispute_opened_event_data):
        """Test handling DisputeOpened event"""
        notification_id = EventService.handle_dispute_opened(
            db_session, dispute_opened_event_data
        )

        assert notification_id is not None

        # Verify notification was created
        from app.services.notification_service import NotificationService

        notification = NotificationService.get_notification(db_session, notification_id)
        assert notification is not None
        assert notification.title == "Dispute Opened"

    def test_handle_safety_report_filed(
        self, db_session, safety_report_filed_event_data
    ):
        """Test handling SafetyReportFiled event"""
        notification_id = EventService.handle_safety_report_filed(
            db_session, safety_report_filed_event_data
        )

        assert notification_id is not None

        # Verify notification was created
        from app.services.notification_service import NotificationService

        notification = NotificationService.get_notification(db_session, notification_id)
        assert notification is not None
        assert notification.title == "Safety Report Filed"

    def test_handle_event_with_missing_data(self, db_session):
        """Test handling event with missing data"""
        notification_id = EventService.handle_user_registered(db_session, {})

        # Should return None when required data is missing
        assert notification_id is None
