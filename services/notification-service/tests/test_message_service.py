import pytest
from datetime import datetime
from app.services.message_service import MessageService
from app.schemas.message import MessageCreate, MessageType


class TestMessageService:
    """Unit tests for MessageService"""

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

    def test_create_message(self, db_session, sample_message_data):
        """Test creating a message"""
        result = MessageService.create_message(db_session, sample_message_data)

        assert result.sender_id == sample_message_data.sender_id
        assert result.recipient_id == sample_message_data.recipient_id
        assert result.content == sample_message_data.content
        assert result.message_type == sample_message_data.message_type
        assert result.is_read == False

    def test_get_message(self, db_session, sample_message_data):
        """Test getting a message by ID"""
        # Create a message first
        created_message = MessageService.create_message(db_session, sample_message_data)

        # Get the message by ID
        result = MessageService.get_message(db_session, str(created_message.message_id))

        assert result.message_id == created_message.message_id
        assert result.content == sample_message_data.content

    def test_get_message_not_found(self, db_session):
        """Test getting a message that doesn't exist"""
        result = MessageService.get_message(db_session, "non-existent-id")
        assert result is None

    def test_get_conversation(self, db_session, sample_message_data):
        """Test getting conversation between two users"""
        # Create messages between two users
        MessageService.create_message(db_session, sample_message_data)

        # Create another message in the same conversation
        second_message = MessageCreate(
            sender_id=sample_message_data.recipient_id,
            recipient_id=sample_message_data.sender_id,
            content="Reply to the test message",
            message_type=MessageType.DIRECT,
        )
        MessageService.create_message(db_session, second_message)

        # Get conversation
        result = MessageService.get_conversation(
            db_session, sample_message_data.sender_id, sample_message_data.recipient_id
        )

        assert len(result.messages) == 2
        assert result.total_count == 2

    def test_mark_as_read(self, db_session, sample_message_data):
        """Test marking a message as read"""
        # Create a message
        created_message = MessageService.create_message(db_session, sample_message_data)

        # Mark as read
        result = MessageService.mark_as_read(
            db_session, str(created_message.message_id)
        )

        assert result.is_read == True
        assert result.read_at is not None

    def test_get_unread_count(self, db_session, sample_message_data):
        """Test getting unread message count"""
        # Create a message
        MessageService.create_message(db_session, sample_message_data)

        # Get unread count
        count = MessageService.get_unread_count(
            db_session, sample_message_data.recipient_id
        )

        assert count == 1

    def test_mark_conversation_as_read(self, db_session, sample_message_data):
        """Test marking all messages in a conversation as read"""
        # Create a message
        MessageService.create_message(db_session, sample_message_data)

        # Mark conversation as read
        count = MessageService.mark_conversation_as_read(
            db_session, sample_message_data.recipient_id, sample_message_data.sender_id
        )

        assert count == 1

    def test_delete_message(self, db_session, sample_message_data):
        """Test deleting a message"""
        # Create a message
        created_message = MessageService.create_message(db_session, sample_message_data)

        # Delete the message
        success = MessageService.delete_message(
            db_session, str(created_message.message_id)
        )

        assert success == True

        # Verify message is deleted
        result = MessageService.get_message(db_session, str(created_message.message_id))
        assert result is None
