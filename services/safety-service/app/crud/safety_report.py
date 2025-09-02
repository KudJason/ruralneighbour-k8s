from typing import List, Optional

from app.models.safety_report import SafetyReport
from app.schemas.safety_report import SafetyReportCreate, SafetyReportUpdate
from sqlalchemy import desc
from sqlalchemy.orm import Session


class SafetyReportCRUD:
    def create(self, db: Session, obj_in: SafetyReportCreate) -> SafetyReport:
        data = obj_in.model_dump()
        for key in [
            "reporter_id",
            "reported_user_id",
            "service_assignment_id",
        ]:
            if data.get(key) is not None:
                data[key] = str(data[key])
        db_obj = SafetyReport(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, report_id: str) -> Optional[SafetyReport]:
        return (
            db.query(SafetyReport).filter(SafetyReport.report_id == report_id).first()
        )

    def list_by_reporter(self, db: Session, reporter_id: str) -> List[SafetyReport]:
        reporter_id_str = str(reporter_id)
        return (
            db.query(SafetyReport)
            .filter(SafetyReport.reporter_id == reporter_id_str)
            .order_by(desc(SafetyReport.created_at))
            .all()
        )

    def update(
        self, db: Session, report_id: str, obj_in: SafetyReportUpdate
    ) -> Optional[SafetyReport]:
        db_obj = self.get(db, report_id)
        if not db_obj:
            return None
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj


safety_report_crud = SafetyReportCRUD()


