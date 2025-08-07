from datetime import datetime
from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict
from enum import Enum


class NotificationType(str, Enum):
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


class DeliveryMethod(str, Enum):
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


class NotificationBase(BaseModel):
    user_id: UUID4
    notification_type: NotificationType
    title: str
    content: Optional[str] = None
    related_id: Optional[UUID4] = None
    delivery_method: DeliveryMethod
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    delivery_status: Optional[DeliveryStatus] = None
    is_read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    notification_id: UUID4
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationSummary(BaseModel):
    total_count: int
    unread_count: int
    notifications: list[NotificationResponse]

    model_config = ConfigDict(from_attributes=True)

