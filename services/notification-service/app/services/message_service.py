from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.message import message_crud
from app.schemas.message import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    ConversationResponse,
)


class MessageService:
    """Service for message management"""

    @staticmethod
    def create_message(db: Session, message_data: MessageCreate) -> MessageResponse:
        """Create a new message"""
        message = message_crud.create(db, message_data)
        return MessageResponse.model_validate(message)

    @staticmethod
    def get_message(db: Session, message_id: str) -> Optional[MessageResponse]:
        """Get a message by ID"""
        message = message_crud.get(db, message_id)
        return MessageResponse.model_validate(message) if message else None

    @staticmethod
    def get_conversation(
        db: Session, user1_id: str, user2_id: str, skip: int = 0, limit: int = 50
    ) -> ConversationResponse:
        """Get conversation between two users"""
        messages = message_crud.get_conversation(db, user1_id, user2_id, skip, limit)
        unread_count = message_crud.get_unread_count(db, user1_id)

        return ConversationResponse(
            messages=[MessageResponse.model_validate(msg) for msg in messages],
            total_count=len(messages),
            unread_count=unread_count,
        )

    @staticmethod
    def get_user_messages(
        db: Session, user_id: str, skip: int = 0, limit: int = 50
    ) -> List[MessageResponse]:
        """Get all messages for a user"""
        messages = message_crud.get_user_messages(db, user_id, skip, limit)
        return [MessageResponse.model_validate(msg) for msg in messages]

    @staticmethod
    def get_unread_count(db: Session, user_id: str) -> int:
        """Get count of unread messages for a user"""
        return message_crud.get_unread_count(db, user_id)

    @staticmethod
    def mark_as_read(db: Session, message_id: str) -> Optional[MessageResponse]:
        """Mark a message as read"""
        message = message_crud.mark_as_read(db, message_id)
        return MessageResponse.model_validate(message) if message else None

    @staticmethod
    def mark_conversation_as_read(db: Session, user_id: str, other_user_id: str) -> int:
        """Mark all messages in a conversation as read"""
        return message_crud.mark_conversation_as_read(db, user_id, other_user_id)

    @staticmethod
    def delete_message(db: Session, message_id: str) -> bool:
        """Delete a message"""
        return message_crud.delete(db, message_id)
