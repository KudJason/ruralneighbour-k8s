from sqlalchemy.orm import Session
from typing import Optional
import uuid
from ..models.user import User


class UserCRUD:

    @staticmethod
    def get_user(db: Session, user_id: uuid.UUID) -> Optional[User]:
        """Get user by user_id"""
        return db.query(User).filter(User.user_id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def update_user_mode(db: Session, user_id: uuid.UUID, mode: str) -> Optional[User]:
        """Update user's default mode"""
        db_user = db.query(User).filter(User.user_id == user_id).first()
        if not db_user:
            return None

        setattr(db_user, "default_mode", mode)
        db.commit()
        db.refresh(db_user)
        return db_user
