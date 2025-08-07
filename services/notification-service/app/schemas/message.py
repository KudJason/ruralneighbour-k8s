from datetime import datetime
from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict
from enum import Enum


class MessageType(str, Enum):
    DIRECT = "direct"
    SYSTEM = "system"
    SERVICE_REQUEST = "service_request"


class MessageBase(BaseModel):
    sender_id: UUID4
    recipient_id: UUID4
    service_request_id: Optional[UUID4] = None
    message_type: MessageType = MessageType.DIRECT
    content: str


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    is_read: Optional[bool] = None


class MessageResponse(MessageBase):
    message_id: UUID4
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    messages: list[MessageResponse]
    total_count: int
    unread_count: int

    model_config = ConfigDict(from_attributes=True)

