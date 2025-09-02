from datetime import date
from typing import List

from app.crud.metric import platform_metric_crud
from app.schemas.metric import PlatformMetricCreate, PlatformMetricResponse
from sqlalchemy.orm import Session


class MetricsService:
    @staticmethod
    def record_metric(
        db: Session, data: PlatformMetricCreate
    ) -> PlatformMetricResponse:
        metric = platform_metric_crud.create(db, data)
        return PlatformMetricResponse.model_validate(metric)

    @staticmethod
    def record_service_completed(
        db: Session, completion_count: int, on_date: date
    ) -> PlatformMetricResponse:
        data = PlatformMetricCreate(
            metric_name="service_completion_count",
            metric_value=float(completion_count),
            measurement_date=on_date,
            measurement_period="daily",
        )
        return MetricsService.record_metric(db, data)


