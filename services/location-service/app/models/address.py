import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
import os

# Only import PostGIS if not in test environment
if os.getenv("TESTING") != "true":
    from geoalchemy2 import Geography

    POSTGIS_AVAILABLE = True
else:
    POSTGIS_AVAILABLE = False

from app.db.base import Base


class UserAddress(Base):
    __tablename__ = "user_addresses"

    address_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    street_address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False, default="USA")

    # PostGIS geography column for spatial queries (only in production)
    if POSTGIS_AVAILABLE:
        location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    else:
        # Use String for testing environment
        location = Column(String(255), nullable=False)

    # Business logic fields
    is_within_service_area = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    address_type = Column(
        String(50), default="residential"
    )  # residential, business, etc.

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserAddress(address_id={self.address_id}, user_id={self.user_id}, city={self.city})>"
