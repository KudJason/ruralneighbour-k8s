import pytest
from datetime import datetime
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationCreate,
    NotificationType,
    DeliveryMethod,
)


class TestNotificationService:
    """Unit tests for NotificationService"""

    @pytest.fixture
    def sample_notification_data(self):
        """Sample notification data for testing"""
        return NotificationCreate(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            notification_type=NotificationType.WELCOME,
            title="Welcome to Our Platform!",
            content="Hi User, welcome to our platform!",
            delivery_method=DeliveryMethod.EMAIL,
        )

    def test_create_notification(self, db_session, sample_notification_data):
        """Test creating a notification"""
        result = NotificationService.create_notification(
            db_session, sample_notification_data
        )

        assert result.user_id == sample_notification_data.user_id
        assert result.notification_type == sample_notification_data.notification_type
        assert result.title == sample_notification_data.title
        assert result.content == sample_notification_data.content
        assert result.delivery_method == sample_notification_data.delivery_method
        assert result.is_read == False

    def test_get_notification(self, db_session, sample_notification_data):
        """Test getting a notification by ID"""
        # Create a notification first
        created_notification = NotificationService.create_notification(
            db_session, sample_notification_data
        )

        # Get the notification by ID
        result = NotificationService.get_notification(
            db_session, str(created_notification.notification_id)
        )

        assert result.notification_id == created_notification.notification_id
        assert result.title == sample_notification_data.title

    def test_get_notification_not_found(self, db_session):
        """Test getting a notification that doesn't exist"""
        result = NotificationService.get_notification(db_session, "non-existent-id")
        assert result is None

    def test_get_user_notifications(self, db_session, sample_notification_data):
        """Test getting notifications for a user"""
        # Create a notification
        NotificationService.create_notification(db_session, sample_notification_data)

        # Get user notifications
        result = NotificationService.get_user_notifications(
            db_session, sample_notification_data.user_id
        )

        assert len(result.notifications) == 1
        assert result.total_count == 1
        assert result.unread_count == 1

    def test_get_unread_notifications(self, db_session, sample_notification_data):
        """Test getting unread notifications for a user"""
        # Create a notification
        NotificationService.create_notification(db_session, sample_notification_data)

        # Get unread notifications
        result = NotificationService.get_unread_notifications(
            db_session, sample_notification_data.user_id
        )

        assert len(result) == 1
        assert result[0].is_read == False

    def test_get_unread_count(self, db_session, sample_notification_data):
        """Test getting unread notification count"""
        # Create a notification
        NotificationService.create_notification(db_session, sample_notification_data)

        # Get unread count
        count = NotificationService.get_unread_count(
            db_session, sample_notification_data.user_id
        )

        assert count == 1

    def test_mark_as_read(self, db_session, sample_notification_data):
        """Test marking a notification as read"""
        # Create a notification
        created_notification = NotificationService.create_notification(
            db_session, sample_notification_data
        )

        # Mark as read
        result = NotificationService.mark_as_read(
            db_session, str(created_notification.notification_id)
        )

        assert result.is_read == True
        assert result.read_at is not None

    def test_mark_all_as_read(self, db_session, sample_notification_data):
        """Test marking all notifications for a user as read"""
        # Create a notification
        NotificationService.create_notification(db_session, sample_notification_data)

        # Mark all as read
        count = NotificationService.mark_all_as_read(
            db_session, sample_notification_data.user_id
        )

        assert count == 1

    def test_update_delivery_status(self, db_session, sample_notification_data):
        """Test updating delivery status of a notification"""
        # Create a notification
        created_notification = NotificationService.create_notification(
            db_session, sample_notification_data
        )

        # Update delivery status
        result = NotificationService.update_delivery_status(
            db_session, str(created_notification.notification_id), "sent"
        )

        assert result.delivery_status == "sent"

    def test_get_by_type(self, db_session, sample_notification_data):
        """Test getting notifications by type"""
        # Create a notification
        NotificationService.create_notification(db_session, sample_notification_data)

        # Get notifications by type
        result = NotificationService.get_by_type(
            db_session, sample_notification_data.user_id, "welcome"
        )

        assert len(result) == 1
        assert result[0].notification_type == NotificationType.WELCOME

    def test_delete_notification(self, db_session, sample_notification_data):
        """Test deleting a notification"""
        # Create a notification
        created_notification = NotificationService.create_notification(
            db_session, sample_notification_data
        )

        # Delete the notification
        success = NotificationService.delete_notification(
            db_session, str(created_notification.notification_id)
        )

        assert success == True

        # Verify notification is deleted
        result = NotificationService.get_notification(
            db_session, str(created_notification.notification_id)
        )
        assert result is None

    def test_cleanup_old_notifications(self, db_session, sample_notification_data):
        """Test cleaning up old notifications"""
        # Create a notification
        NotificationService.create_notification(db_session, sample_notification_data)

        # Cleanup old notifications (should not delete recent ones)
        count = NotificationService.cleanup_old_notifications(db_session, days=1)

        # Should not delete recent notifications
        assert count == 0
