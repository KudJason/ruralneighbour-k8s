# --- Basic SQLAlchemy models and enums for request-service ---
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.db.base_class import Base


class ServiceRequestStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AssignmentStatus(enum.Enum):
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ServiceType(enum.Enum):
    TRANSPORTATION = "transportation"
    ERRANDS = "errands"
    OTHER = "other"


class PaymentStatus(enum.Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    PAYMENT_FAILED = "payment_failed"


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    request_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requester_id = Column(String(36), nullable=False)
    title = Column(String(255))
    description = Column(Text)
    service_type = Column(Enum(ServiceType), nullable=False)
    pickup_latitude = Column(Float, nullable=False)
    pickup_longitude = Column(Float, nullable=False)
    destination_latitude = Column(Float)
    destination_longitude = Column(Float)
    offered_amount = Column(Float)
    status = Column(Enum(ServiceRequestStatus), default=ServiceRequestStatus.PENDING)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.UNPAID)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ServiceAssignment(Base):
    __tablename__ = "service_assignments"

    assignment_id = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    request_id = Column(
        String(36), ForeignKey("service_requests.request_id"), nullable=False
    )
    provider_id = Column(String(36), nullable=False)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.ASSIGNED)
    provider_notes = Column(Text)
    completion_notes = Column(Text)
    estimated_completion_time = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Rating(Base):
    __tablename__ = "ratings"

    rating_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assignment_id = Column(
        String(36), ForeignKey("service_assignments.assignment_id"), nullable=False
    )
    rater_id = Column(String(36), nullable=False)
    ratee_id = Column(String(36), nullable=False)
    rating_score = Column(Integer, nullable=False)  # 1-5 rating
    review_text = Column(Text)
    is_provider_rating = Column(Integer, default=0)  # 0=False, 1=True
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def is_provider_rating_bool(self) -> bool:
        """Return is_provider_rating as boolean"""
        return bool(self.is_provider_rating)
