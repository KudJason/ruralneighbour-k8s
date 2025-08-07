import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
import os
import enum

# Use String for UUID in testing environment
if os.getenv("TESTING") == "true":
    UUIDType = String(36)  # UUID as string

    def uuid_default():
        return str(uuid.uuid4())

else:
    from sqlalchemy.dialects.postgresql import UUID as UUIDType

    def uuid_default():
        return uuid.uuid4()


from app.db.base import Base


class MessageType(enum.Enum):
    DIRECT = "direct"
    SYSTEM = "system"
    SERVICE_REQUEST = "service_request"


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(UUIDType, primary_key=True, default=uuid_default)
    sender_id = Column(UUIDType, nullable=False)  # References users(user_id)
    recipient_id = Column(UUIDType, nullable=False)  # References users(user_id)
    service_request_id = Column(
        UUIDType, nullable=True
    )  # Optional link to service request
    message_type = Column(
        String(50), nullable=False, default="direct"
    )  # Store as string for SQLite
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Message(message_id={self.message_id}, sender_id={self.sender_id}, recipient_id={self.recipient_id})>"
