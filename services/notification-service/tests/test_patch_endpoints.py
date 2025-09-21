import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.message import MessageCreate, MessageUpdate, MessageType
from app.schemas.notification import NotificationCreate, NotificationUpdate, NotificationType, DeliveryMethod, DeliveryStatus

client = TestClient(app)


class TestPatchEndpoints:
    """Test PATCH endpoints for messages and notifications"""

    @pytest.fixture
    def sample_message_data(self):
        """Sample message data for testing"""
        return MessageCreate(
            sender_id="550e8400-e29b-41d4-a716-446655440000",
            recipient_id="550e8400-e29b-41d4-a716-446655440001",
            service_request_id=None,
            message_type=MessageType.DIRECT,
            content="Hello, this is a test message",
        )

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

    def test_patch_message_content(self, db_session, sample_message_data):
        """Test updating message content via PATCH"""
        # Create a message first
        created_message = client.post(
            "/api/v1/messages",
            json=sample_message_data.model_dump(mode='json'),
            headers={"Authorization": "admin_test_token"}
        )
        assert created_message.status_code == 200
        message_id = created_message.json()["message_id"]

        # Update message content
        update_data = MessageUpdate(content="Updated message content")
        response = client.patch(
            f"/api/v1/messages/{message_id}",
            json=update_data.model_dump(exclude_unset=True, mode='json'),
            headers={"Authorization": "admin_test_token"}
        )

        assert response.status_code == 200
        updated_message = response.json()
        assert updated_message["content"] == "Updated message content"
        assert updated_message["message_id"] == message_id

    def test_patch_message_is_read(self, db_session, sample_message_data):
        """Test updating message is_read status via PATCH"""
        # Create a message first
        created_message = client.post(
            "/api/v1/messages",
            json=sample_message_data.model_dump(mode='json'),
            headers={"Authorization": "admin_test_token"}
        )
        assert created_message.status_code == 200
        message_id = created_message.json()["message_id"]
        assert created_message.json()["is_read"] == False

        # Mark message as read
        update_data = MessageUpdate(is_read=True)
        response = client.patch(
            f"/api/v1/messages/{message_id}",
            json=update_data.model_dump(exclude_unset=True, mode='json'),
            headers={"Authorization": "admin_test_token"}
        )

        assert response.status_code == 200
        updated_message = response.json()
        assert updated_message["is_read"] == True
        assert updated_message["read_at"] is not None

    def test_patch_message_not_found(self, db_session):
        """Test PATCH message with non-existent ID"""
        update_data = MessageUpdate(content="Updated content")
        response = client.patch(
            "/api/v1/messages/non-existent-id",
            json=update_data.model_dump(exclude_unset=True, mode='json'),
            headers={"Authorization": "admin_test_token"}
        )

        assert response.status_code == 404
        assert "Message not found" in response.json()["detail"]

    def test_patch_notification_title(self, db_session, sample_notification_data):
        """Test updating notification title via PATCH"""
        # Create a notification first
        created_notification = client.post(
            "/api/v1/notifications",
            json=sample_notification_data.model_dump(mode='json'),
            headers={"Authorization": "admin_test_token"}
        )
        assert created_notification.status_code == 200
        notification_id = created_notification.json()["notification_id"]

        # Update notification title
        update_data = NotificationUpdate(title="Updated Title")
        response = client.patch(
            f"/api/v1/notifications/{notification_id}",
            json=update_data.model_dump(exclude_unset=True, mode='json'),
            headers={"Authorization": "admin_test_token"}
        )

        assert response.status_code == 200
        updated_notification = response.json()
        assert updated_notification["title"] == "Updated Title"
        assert updated_notification["notification_id"] == notification_id

    def test_patch_notification_content(self, db_session, sample_notification_data):
        """Test updating notification content via PATCH"""
        # Create a notification first
        created_notification = client.post(
            "/api/v1/notifications",
            json=sample_notification_data.model_dump(mode='json'),
            headers={"Authorization": "admin_test_token"}
        )
        assert created_notification.status_code == 200
        notification_id = created_notification.json()["notification_id"]

        # Update notification content
        update_data = NotificationUpdate(content="Updated notification content")
        response = client.patch(
            f"/api/v1/notifications/{notification_id}",
            json=update_data.model_dump(exclude_unset=True, mode='json'),
            headers={"Authorization": "admin_test_token"}
        )

        assert response.status_code == 200
        updated_notification = response.json()
        assert updated_notification["content"] == "Updated notification content"

    def test_patch_notification_is_read(self, db_session, sample_notification_data):
        """Test updating notification is_read status via PATCH"""
        # Create a notification first
        created_notification = client.post(
            "/api/v1/notifications",
            json=sample_notification_data.model_dump(mode='json'),
            headers={"Authorization": "admin_test_token"}
        )
        assert created_notification.status_code == 200
        notification_id = created_notification.json()["notification_id"]
        assert created_notification.json()["is_read"] == False

        # Mark notification as read
        update_data = NotificationUpdate(is_read=True)
        response = client.patch(
            f"/api/v1/notifications/{notification_id}",
            json=update_data.model_dump(exclude_unset=True, mode='json'),
            headers={"Authorization": "admin_test_token"}
        )

        assert response.status_code == 200
        updated_notification = response.json()
        assert updated_notification["is_read"] == True
        assert updated_notification["read_at"] is not None

    def test_patch_notification_delivery_status(self, db_session, sample_notification_data):
        """Test updating notification delivery status via PATCH"""
        # Create a notification first
        created_notification = client.post(
            "/api/v1/notifications",
            json=sample_notification_data.model_dump(mode='json'),
            headers={"Authorization": "admin_test_token"}
        )
        assert created_notification.status_code == 200
        notification_id = created_notification.json()["notification_id"]

        # Update delivery status
        update_data = NotificationUpdate(delivery_status=DeliveryStatus.SENT)
        response = client.patch(
            f"/api/v1/notifications/{notification_id}",
            json=update_data.model_dump(exclude_unset=True, mode='json'),
            headers={"Authorization": "admin_test_token"}
        )

        assert response.status_code == 200
        updated_notification = response.json()
        assert updated_notification["delivery_status"] == "sent"

    def test_patch_notification_not_found(self, db_session):
        """Test PATCH notification with non-existent ID"""
        update_data = NotificationUpdate(title="Updated Title")
        response = client.patch(
            "/api/v1/notifications/non-existent-id",
            json=update_data.model_dump(exclude_unset=True, mode='json'),
            headers={"Authorization": "admin_test_token"}
        )

        assert response.status_code == 404
        assert "Notification not found" in response.json()["detail"]

    def test_patch_message_unauthorized(self, db_session, sample_message_data):
        """Test PATCH message without authorization"""
        # Create a message first
        created_message = client.post(
            "/api/v1/messages",
            json=sample_message_data.model_dump(mode='json'),
            headers={"Authorization": "admin_test_token"}
        )
        message_id = created_message.json()["message_id"]

        # Try to update without authorization
        update_data = MessageUpdate(content="Updated content")
        response = client.patch(
            f"/api/v1/messages/{message_id}",
            json=update_data.model_dump(exclude_unset=True)
        )

        assert response.status_code == 401

    def test_patch_notification_unauthorized(self, db_session, sample_notification_data):
        """Test PATCH notification without authorization"""
        # Create a notification first
        created_notification = client.post(
            "/api/v1/notifications",
            json=sample_notification_data.model_dump(mode='json'),
            headers={"Authorization": "admin_test_token"}
        )
        notification_id = created_notification.json()["notification_id"]

        # Try to update without authorization
        update_data = NotificationUpdate(title="Updated Title")
        response = client.patch(
            f"/api/v1/notifications/{notification_id}",
            json=update_data.model_dump(exclude_unset=True)
        )

        assert response.status_code == 401
