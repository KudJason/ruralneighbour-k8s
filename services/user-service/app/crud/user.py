from sqlalchemy.orm import Session
from typing import Optional
import uuid
from ..models.user import User
from ..schemas.user import UserUpdate
from passlib.hash import bcrypt


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

    @staticmethod
    def update_user(db: Session, user_id: uuid.UUID, update: UserUpdate) -> Optional[User]:
        """General user update supporting partial fields."""
        db_user = db.query(User).filter(User.user_id == user_id).first()
        if not db_user:
            return None

        update_data = update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def create_user(
        db: Session,
        *,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        default_mode: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> User:
        """Create user with hashed password."""
        password_hash = bcrypt.hash(password)
        db_user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            default_mode=default_mode or "NIN",
            is_active=True if is_active is None else bool(is_active),
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
