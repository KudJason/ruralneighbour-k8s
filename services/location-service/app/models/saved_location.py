import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class SavedLocation(Base):
    __tablename__ = "saved_locations"

    location_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    latitude = Column(String(50), nullable=False)
    longitude = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SavedLocation(location_id={self.location_id}, user_id={self.user_id}, name={self.name})>"








