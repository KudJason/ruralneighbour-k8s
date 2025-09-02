# --- Basic Pydantic schemas for request-service ---
import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ServiceRequestCreate(BaseModel):
    title: str
    description: Optional[str]
    service_type: str
    pickup_latitude: float
    pickup_longitude: float
    destination_latitude: Optional[float]
    destination_longitude: Optional[float]
    offered_amount: Optional[float]


class ServiceRequestUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    offered_amount: Optional[float]


class ServiceRequestResponse(BaseModel):
    id: int
    request_id: str
    requester_id: str
    title: str
    description: Optional[str]
    service_type: str
    pickup_latitude: float
    pickup_longitude: float
    destination_latitude: Optional[float]
    destination_longitude: Optional[float]
    offered_amount: Optional[float]
    status: str
    payment_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# New output schemas referenced in routers
class ServiceRequestOut(ServiceRequestResponse):
    pass


class ServiceRequestList(BaseModel):
    requests: List[ServiceRequestResponse]
    total: int
    page: int
    size: int


class MessageResponse(BaseModel):
    message: str


class ServiceAssignmentCreate(BaseModel):
    request_id: str
    estimated_completion_time: Optional[datetime | str]
    provider_notes: Optional[str]

    @field_validator("estimated_completion_time", mode="before")
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except Exception:
                return v  # let downstream handle invalid format
        return v


class ServiceAssignmentUpdate(BaseModel):
    status: str
    provider_notes: Optional[str]
    estimated_completion_time: Optional[datetime | str]
    completion_notes: Optional[str]

    @field_validator("estimated_completion_time", mode="before")
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except Exception:
                return v
        return v


class ServiceAssignmentResponse(BaseModel):
    assignment_id: str
    request_id: str
    provider_id: str
    status: str
    provider_notes: Optional[str]
    completion_notes: Optional[str]
    estimated_completion_time: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ServiceAssignmentOut(ServiceAssignmentResponse):
    pass


class RatingCreate(BaseModel):
    assignment_id: str
    ratee_id: str
    rating_score: int
    review_text: Optional[str]
    is_provider_rating: bool


class RatingResponse(BaseModel):
    rating_id: str
    assignment_id: str
    rater_id: str
    ratee_id: str
    rating_score: int
    review_text: Optional[str]
    is_provider_rating: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class RatingOut(RatingResponse):
    pass


class StatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str]


# Additional provider view schemas
class AvailableRequest(BaseModel):
    request_id: str
    title: str
    description: Optional[str]
    service_type: str
    pickup_latitude: float
    pickup_longitude: float
    offered_amount: Optional[float]
    status: str
    requester_id: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class AvailableRequestsList(BaseModel):
    requests: List[AvailableRequest]
    total: int
    page: int
    size: int


class AvailableRequestOut(AvailableRequest):
    pass
