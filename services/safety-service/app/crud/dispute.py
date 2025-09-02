from datetime import datetime
from typing import List, Optional

from app.models.dispute import Dispute
from app.schemas.dispute import DisputeCreate, DisputeUpdate
from sqlalchemy import desc
from sqlalchemy.orm import Session


class DisputeCRUD:
    def create(self, db: Session, obj_in: DisputeCreate) -> Dispute:
        data = obj_in.model_dump()
        for key in [
            "service_assignment_id",
            "complainant_id",
            "respondent_id",
            "resolved_by",
        ]:
            if data.get(key) is not None:
                data[key] = str(data[key])
        db_obj = Dispute(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, dispute_id: str) -> Optional[Dispute]:
        return db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()

    def list_by_user(self, db: Session, user_id: str) -> List[Dispute]:
        user_id_str = str(user_id)
        return (
            db.query(Dispute)
            .filter(
                (Dispute.complainant_id == user_id_str)
                | (Dispute.respondent_id == user_id_str)
            )
            .order_by(desc(Dispute.created_at))
            .all()
        )

    def update(
        self, db: Session, dispute_id: str, obj_in: DisputeUpdate
    ) -> Optional[Dispute]:
        db_obj = self.get(db, dispute_id)
        if not db_obj:
            return None
        update_data = obj_in.model_dump(exclude_unset=True)
        if update_data.get("status") == "resolved" and db_obj.resolved_at is None:
            setattr(db_obj, "resolved_at", datetime.utcnow())
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj


dispute_crud = DisputeCRUD()
