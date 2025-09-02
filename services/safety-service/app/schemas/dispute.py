from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import UUID4, BaseModel, ConfigDict


class DisputeStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"


class DisputeBase(BaseModel):
    service_assignment_id: UUID4
    complainant_id: UUID4
    respondent_id: UUID4
    dispute_type: str
    description: str
    status: DisputeStatus = DisputeStatus.OPEN
    resolution_notes: Optional[str] = None
    resolved_by: Optional[UUID4] = None


class DisputeCreate(DisputeBase):
    pass


class DisputeUpdate(BaseModel):
    status: Optional[DisputeStatus] = None
    resolution_notes: Optional[str] = None
    resolved_by: Optional[UUID4] = None


class DisputeResponse(DisputeBase):
    dispute_id: UUID4
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


