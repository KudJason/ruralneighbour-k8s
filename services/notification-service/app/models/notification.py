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


class NotificationType(enum.Enum):
    WELCOME = "welcome"
    PROFILE_UPDATE = "profile_update"
    MODE_CHANGE = "mode_change"
    SERVICE_REQUEST_CREATED = "service_request_created"
    SERVICE_COMPLETED = "service_completed"
    RATING_CREATED = "rating_created"
    PAYMENT_PROCESSED = "payment_processed"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_REFUNDED = "payment_refunded"
    DISPUTE_OPENED = "dispute_opened"
    DISPUTE_RESOLVED = "dispute_resolved"
    SAFETY_REPORT = "safety_report"


class DeliveryMethod(enum.Enum):
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"


class DeliveryStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(UUIDType, primary_key=True, default=uuid_default)
    user_id = Column(UUIDType, nullable=False)  # References users(user_id)
    notification_type = Column(String(50), nullable=False)  # Store as string for SQLite
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    related_id = Column(UUIDType, nullable=True)  # ID of related entity
    delivery_method = Column(String(50), nullable=False)  # Store as string for SQLite
    delivery_status = Column(
        String(50), default="pending"
    )  # Store as string for SQLite
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification(notification_id={self.notification_id}, user_id={self.user_id}, type={self.notification_type})>"
