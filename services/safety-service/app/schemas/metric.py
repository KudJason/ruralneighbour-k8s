from datetime import date

from pydantic import UUID4, BaseModel, ConfigDict


class PlatformMetricBase(BaseModel):
    metric_name: str
    metric_value: float
    measurement_date: date = date.today()
    measurement_period: str = "daily"


class PlatformMetricCreate(PlatformMetricBase):
    pass


class PlatformMetricResponse(PlatformMetricBase):
    metric_id: UUID4

    model_config = ConfigDict(from_attributes=True)


