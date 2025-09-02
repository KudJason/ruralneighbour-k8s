from typing import List, Optional

from app.models.metric import PlatformMetric
from app.schemas.metric import PlatformMetricCreate
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session


class PlatformMetricCRUD:
    def create(self, db: Session, obj_in: PlatformMetricCreate) -> PlatformMetric:
        data = obj_in.model_dump()
        db_obj = PlatformMetric(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def list_by_name(self, db: Session, metric_name: str) -> List[PlatformMetric]:
        return (
            db.query(PlatformMetric)
            .filter(PlatformMetric.metric_name == metric_name)
            .order_by(desc(PlatformMetric.measurement_date))
            .all()
        )


platform_metric_crud = PlatformMetricCRUD()


