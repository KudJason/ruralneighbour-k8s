# --- Basic Pydantic schemas for request-service ---
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ServiceRequestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    service_type: str = Field(alias="serviceType")
    pickup_latitude: float = Field(alias="pickupLatitude")
    pickup_longitude: float = Field(alias="pickupLongitude")
    destination_latitude: Optional[float] = Field(
        alias="destinationLatitude", default=None
    )
    destination_longitude: Optional[float] = Field(
        alias="destinationLongitude", default=None
    )
    offered_amount: Optional[float] = Field(alias="offeredAmount", default=None)

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ServiceRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    offered_amount: Optional[float] = Field(alias="offeredAmount", default=None)
    status: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ServiceRequestResponse(BaseModel):
    id: int
    request_id: str = Field(alias="requestId")
    requester_id: str = Field(alias="requesterId")
    title: str
    description: Optional[str]
    service_type: str = Field(alias="serviceType")
    pickup_latitude: float = Field(alias="pickupLatitude")
    pickup_longitude: float = Field(alias="pickupLongitude")
    destination_latitude: Optional[float] = Field(alias="destinationLatitude")
    destination_longitude: Optional[float] = Field(alias="destinationLongitude")
    offered_amount: Optional[float] = Field(alias="offeredAmount")
    status: str
    payment_status: Optional[str] = Field(alias="paymentStatus", default=None)
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


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
    request_id: str = Field(alias="requestId")
    estimated_completion_time: Optional[datetime | str] = Field(
        alias="estimatedCompletionTime"
    )
    provider_notes: Optional[str] = Field(alias="providerNotes")

    @field_validator("estimated_completion_time", mode="before")
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except Exception:
                return v  # let downstream handle invalid format
        return v

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ServiceAssignmentUpdate(BaseModel):
    status: str
    provider_notes: Optional[str] = Field(alias="providerNotes")
    estimated_completion_time: Optional[datetime | str] = Field(
        alias="estimatedCompletionTime"
    )
    completion_notes: Optional[str] = Field(alias="completionNotes")

    @field_validator("estimated_completion_time", mode="before")
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except Exception:
                return v
        return v

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ServiceAssignmentResponse(BaseModel):
    assignment_id: str = Field(alias="assignmentId")
    request_id: str = Field(alias="requestId")
    provider_id: str = Field(alias="providerId")
    status: str
    provider_notes: Optional[str] = Field(alias="providerNotes")
    completion_notes: Optional[str] = Field(alias="completionNotes")
    estimated_completion_time: Optional[datetime] = Field(
        alias="estimatedCompletionTime"
    )
    completed_at: Optional[datetime] = Field(alias="completedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ServiceAssignmentOut(ServiceAssignmentResponse):
    pass


class RatingCreate(BaseModel):
    assignment_id: str = Field(alias="assignmentId")
    ratee_id: str = Field(alias="rateeId")
    rating_score: int = Field(alias="ratingScore")
    review_text: Optional[str] = Field(alias="reviewText")
    is_provider_rating: bool = Field(alias="isProviderRating")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class RatingResponse(BaseModel):
    rating_id: str = Field(alias="ratingId")
    assignment_id: str = Field(alias="assignmentId")
    rater_id: str = Field(alias="raterId")
    ratee_id: str = Field(alias="rateeId")
    rating_score: int = Field(alias="ratingScore")
    review_text: Optional[str] = Field(alias="reviewText")
    is_provider_rating: bool = Field(alias="isProviderRating")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class RatingOut(RatingResponse):
    pass


class StatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str]


# Additional provider view schemas
class AvailableRequest(BaseModel):
    request_id: str = Field(alias="requestId")
    title: str
    description: Optional[str]
    service_type: str = Field(alias="serviceType")
    pickup_latitude: float = Field(alias="pickupLatitude")
    pickup_longitude: float = Field(alias="pickupLongitude")
    offered_amount: Optional[float] = Field(alias="offeredAmount")
    status: str
    requester_id: str = Field(alias="requesterId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class AvailableRequestsList(BaseModel):
    requests: List[AvailableRequest]
    total: int
    page: int
    size: int


class AvailableRequestOut(AvailableRequest):
    pass
