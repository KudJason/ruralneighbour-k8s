from typing import List, Optional
from sqlalchemy.orm import Session
import uuid

from app.models.saved_location import SavedLocation


class SavedLocationCRUD:
    @staticmethod
    def create(db: Session, *, user_id: uuid.UUID, address: str, latitude: float, longitude: float, name: Optional[str] = None) -> SavedLocation:
        item = SavedLocation(
            user_id=user_id,
            name=name or address,
            address=address,
            latitude=str(latitude),
            longitude=str(longitude),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def list_by_user(db: Session, *, user_id: uuid.UUID) -> List[SavedLocation]:
        return db.query(SavedLocation).filter(SavedLocation.user_id == user_id).all()

    @staticmethod
    def delete(db: Session, *, user_id: uuid.UUID, location_id: uuid.UUID) -> bool:
        obj = (
            db.query(SavedLocation)
            .filter(SavedLocation.location_id == location_id, SavedLocation.user_id == user_id)
            .first()
        )
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True


saved_location_crud = SavedLocationCRUD()








