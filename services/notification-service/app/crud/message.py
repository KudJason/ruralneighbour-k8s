from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageUpdate


class MessageCRUD:
    def create(self, db: Session, obj_in: MessageCreate) -> Message:
        """Create a new message"""
        # Convert message_type enum to string for SQLite compatibility
        data = obj_in.model_dump()
        if data.get("message_type"):
            data["message_type"] = data["message_type"].value

        # Ensure UUID fields are strings for SQLite compatibility
        if data.get("sender_id"):
            data["sender_id"] = str(data["sender_id"])
        if data.get("recipient_id"):
            data["recipient_id"] = str(data["recipient_id"])
        if data.get("service_request_id"):
            data["service_request_id"] = str(data["service_request_id"])

        db_obj = Message(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, message_id: str) -> Optional[Message]:
        """Get a message by ID"""
        return db.query(Message).filter(Message.message_id == message_id).first()

    def get_conversation(
        self, db: Session, user1_id: str, user2_id: str, skip: int = 0, limit: int = 50
    ) -> List[Message]:
        """Get conversation between two users"""
        # Ensure user IDs are strings for SQLite compatibility
        user1_id_str = str(user1_id)
        user2_id_str = str(user2_id)
        return (
            db.query(Message)
            .filter(
                or_(
                    and_(
                        Message.sender_id == user1_id_str,
                        Message.recipient_id == user2_id_str,
                    ),
                    and_(
                        Message.sender_id == user2_id_str,
                        Message.recipient_id == user1_id_str,
                    ),
                )
            )
            .order_by(desc(Message.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_user_messages(
        self, db: Session, user_id: str, skip: int = 0, limit: int = 50
    ) -> List[Message]:
        """Get all messages for a user (sent and received)"""
        # Ensure user_id is a string for SQLite compatibility
        user_id_str = str(user_id)
        return (
            db.query(Message)
            .filter(
                or_(
                    Message.sender_id == user_id_str,
                    Message.recipient_id == user_id_str,
                )
            )
            .order_by(desc(Message.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_unread_count(self, db: Session, user_id: str) -> int:
        """Get count of unread messages for a user"""
        # Ensure user_id is a string for SQLite compatibility
        user_id_str = str(user_id)
        return (
            db.query(Message)
            .filter(and_(Message.recipient_id == user_id_str, Message.is_read == False))
            .count()
        )

    def mark_as_read(self, db: Session, message_id: str) -> Optional[Message]:
        """Mark a message as read"""
        db_obj = self.get(db, message_id)
        if not db_obj:
            return None

        db_obj.is_read = True
        db_obj.read_at = datetime.utcnow()
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def mark_conversation_as_read(
        self, db: Session, user_id: str, other_user_id: str
    ) -> int:
        """Mark all messages in a conversation as read"""
        # Ensure user IDs are strings for SQLite compatibility
        user_id_str = str(user_id)
        other_user_id_str = str(other_user_id)
        result = (
            db.query(Message)
            .filter(
                and_(
                    Message.sender_id == other_user_id_str,
                    Message.recipient_id == user_id_str,
                    Message.is_read == False,
                )
            )
            .update(
                {
                    Message.is_read: True,
                    Message.read_at: datetime.utcnow(),
                }
            )
        )
        db.commit()
        return result

    def delete(self, db: Session, message_id: str) -> bool:
        """Delete a message"""
        db_obj = self.get(db, message_id)
        if not db_obj:
            return False

        db.delete(db_obj)
        db.commit()
        return True


message_crud = MessageCRUD()
