import os
import uuid
from datetime import date

from app.db.base import Base
from sqlalchemy import Column, Date, Numeric, String

_testing = os.getenv("TESTING") == "true"
if _testing:
    from sqlalchemy import String as UUIDType
else:
    from sqlalchemy.dialects.postgresql import UUID as UUIDType


def uuid_default():
    return str(uuid.uuid4()) if _testing else uuid.uuid4()


class PlatformMetric(Base):
    __tablename__ = "platform_metrics"

    metric_id = Column(UUIDType, primary_key=True, default=uuid_default)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Numeric(15, 4), nullable=False)
    measurement_date = Column(Date, nullable=False, default=date.today)
    measurement_period = Column(String(50), default="daily")
