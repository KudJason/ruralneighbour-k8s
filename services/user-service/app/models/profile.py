from sqlalchemy import (
    Column,
    String,
    Text,
    Numeric,
    Integer,
    ForeignKey,
    TIMESTAMP,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
import uuid
from ..db.base import Base

# Create ENUM types
user_mode = ENUM("NIN", "LAH", name="user_mode", create_type=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    bio = Column(Text)
    average_rating = Column(Numeric(3, 2), default=0.00)
    total_ratings = Column(Integer, default=0)
    default_mode = Column(user_mode, default="NIN")
    phone_number = Column(String(20))
    profile_picture_url = Column(String(500))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProviderProfile(Base):
    __tablename__ = "provider_profile"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    service_radius_miles = Column(Numeric(4, 2), default=2.0)
    vehicle_description = Column(String(500))
    services_offered = Column(Text)  # JSON array as text
    hourly_rate = Column(Numeric(8, 2))
    availability_schedule = Column(Text)  # JSON as text
    is_available = Column(String(10), default="true")  # 'true'/'false' as string
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )
