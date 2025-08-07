# This file references the users table from auth-service
# The actual User model is in auth-service, this is just for reference

from sqlalchemy import Column, String, Boolean, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, ENUM
import uuid
from ..db.base import Base

# User mode ENUM
user_mode = ENUM("NIN", "LAH", name="user_mode", create_type=False)


# Reference model for the users table (managed by auth-service)
class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    default_mode = Column(user_mode, default="NIN")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login = Column(TIMESTAMP(timezone=True))
