from datetime import date

from app.schemas.metric import PlatformMetricCreate
from app.services.metrics_service import MetricsService


def test_record_metric(db_session):
    created = MetricsService.record_metric(
        db_session,
        PlatformMetricCreate(
            metric_name="user_registered_count",
            metric_value=1.0,
            measurement_date=date.today(),
            measurement_period="daily",
        ),
    )
    assert created.metric_name == "user_registered_count"


