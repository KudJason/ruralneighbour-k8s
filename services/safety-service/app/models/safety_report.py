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


class SafetyReport(Base):
    __tablename__ = "safety_reports"

    report_id = Column(UUIDType, primary_key=True, default=uuid_default)
    reporter_id = Column(UUIDType, nullable=False)
    reported_user_id = Column(UUIDType, nullable=True)
    service_assignment_id = Column(UUIDType, nullable=True)
    incident_type = Column(String(50), nullable=False)
    incident_severity = Column(String(50), default="medium")
    incident_description = Column(Text, nullable=False)
    status = Column(String(50), default="reported")
    created_at = Column(DateTime, default=datetime.utcnow)
