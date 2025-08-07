# --- Basic Pydantic schemas for request-service ---
import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, field_validator


class ServiceRequestCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    service_type: str = Field(
        ..., description="Type of service: transportation, errands, other"
    )
    pickup_latitude: float = Field(..., ge=-90, le=90)
    pickup_longitude: float = Field(..., ge=-180, le=180)
    destination_latitude: Optional[float] = Field(None, ge=-90, le=90)
    destination_longitude: Optional[float] = Field(None, ge=-180, le=180)
    offered_amount: Optional[float] = Field(None, ge=0)


class ServiceRequestUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    offered_amount: Optional[float] = Field(None, ge=0)
    status: Optional[str] = None


class ServiceRequestResponse(BaseModel):
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
    payment_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ServiceRequestOut(BaseModel):
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
    payment_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ServiceRequestList(BaseModel):
    requests: List[ServiceRequestOut]
    total: int
    page: int
    size: int


class ServiceAssignmentCreate(BaseModel):
    request_id: str
    provider_notes: Optional[str] = None
    estimated_completion_time: Optional[datetime] = None


class ServiceAssignmentUpdate(BaseModel):
    status: Optional[str] = None
    provider_notes: Optional[str] = None
    estimated_completion_time: Optional[datetime] = None
    completion_notes: Optional[str] = None


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


class ServiceAssignmentOut(BaseModel):
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


class RatingCreate(BaseModel):
    assignment_id: str
    ratee_id: str
    rating_score: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None
    is_provider_rating: bool = False


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

    @field_validator("is_provider_rating", mode="before")
    @classmethod
    def convert_is_provider_rating(cls, v):
        if isinstance(v, int):
            return bool(v)
        return v


class RatingOut(BaseModel):
    rating_id: str
    assignment_id: str
    rater_id: str
    ratee_id: str
    rating_score: int
    review_text: Optional[str]
    is_provider_rating: bool
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("is_provider_rating", mode="before")
    @classmethod
    def convert_is_provider_rating(cls, v):
        if isinstance(v, int):
            return bool(v)
        return v


class StatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None


class MessageResponse(BaseModel):
    message: str


class AvailableRequestOut(BaseModel):
    request_id: str
    title: str
    description: Optional[str]
    service_type: str
    pickup_latitude: float
    pickup_longitude: float
    destination_latitude: Optional[float]
    destination_longitude: Optional[float]
    offered_amount: Optional[float]
    created_at: datetime
    distance_miles: Optional[float] = None


class AvailableRequestsList(BaseModel):
    requests: List[AvailableRequestOut]
    total: int
    page: int
    size: int
