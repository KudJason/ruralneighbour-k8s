from typing import List, Optional

from app.crud.dispute import dispute_crud
from app.schemas.dispute import DisputeCreate, DisputeResponse, DisputeUpdate
from sqlalchemy.orm import Session


class DisputeService:
    @staticmethod
    def file_dispute(db: Session, data: DisputeCreate) -> DisputeResponse:
        dispute = dispute_crud.create(db, data)
        return DisputeResponse.model_validate(dispute)

    @staticmethod
    def get_dispute(db: Session, dispute_id: str) -> Optional[DisputeResponse]:
        dispute = dispute_crud.get(db, dispute_id)
        return DisputeResponse.model_validate(dispute) if dispute else None

    @staticmethod
    def list_user_disputes(db: Session, user_id: str) -> List[DisputeResponse]:
        disputes = dispute_crud.list_by_user(db, user_id)
        return [DisputeResponse.model_validate(d) for d in disputes]

    @staticmethod
    def update_dispute(
        db: Session, dispute_id: str, data: DisputeUpdate
    ) -> Optional[DisputeResponse]:
        dispute = dispute_crud.update(db, dispute_id, data)
        return DisputeResponse.model_validate(dispute) if dispute else None


