from datetime import datetime
from typing import Optional

from pydantic import UUID4, BaseModel, ConfigDict


class SafetyReportBase(BaseModel):
    reporter_id: UUID4
    reported_user_id: Optional[UUID4] = None
    service_assignment_id: Optional[UUID4] = None
    incident_type: str
    incident_severity: str = "medium"
    incident_description: str
    status: str = "reported"


class SafetyReportCreate(SafetyReportBase):
    pass


class SafetyReportUpdate(BaseModel):
    incident_severity: Optional[str] = None
    status: Optional[str] = None


class SafetyReportResponse(SafetyReportBase):
    report_id: UUID4
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


