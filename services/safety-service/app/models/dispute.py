import os
import uuid
from datetime import datetime

from app.db.base import Base
from sqlalchemy import Column, DateTime, String, Text

_testing = os.getenv("TESTING") == "true"
if _testing:
    from sqlalchemy import String as UUIDType
else:
    from sqlalchemy.dialects.postgresql import UUID as UUIDType


def uuid_default():
    return str(uuid.uuid4()) if _testing else uuid.uuid4()


class Dispute(Base):
    __tablename__ = "disputes"

    dispute_id = Column(UUIDType, primary_key=True, default=uuid_default)
    service_assignment_id = Column(UUIDType, nullable=False)
    complainant_id = Column(UUIDType, nullable=False)
    respondent_id = Column(UUIDType, nullable=False)
    dispute_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="open")
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(UUIDType, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
