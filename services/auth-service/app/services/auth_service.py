from ..models.user import User
from ..schemas.user import UserCreate
from ..core.security import get_password_hash, verify_password
from .events import EventPublisher
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from uuid import uuid4
from datetime import datetime


from app.crud.crud_user import get_user_by_email, create_user, update_last_login


class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        existing_user = get_user_by_email(db, user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        try:
            user = create_user(db, user_in, get_password_hash(user_in.password))
            if user.full_name is not None:
                EventPublisher.publish_user_registered(
                    user_id=str(user.user_id),
                    email=str(user.email),
                    full_name=str(user.full_name),
                )
            else:
                EventPublisher.publish_user_registered(
                    user_id=str(user.user_id), email=str(user.email)
                )
            return user
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User | None:
        user = get_user_by_email(db, email)
        if not user:
            return None
        password_hash = str(getattr(user, "password_hash", ""))
        if not verify_password(password, password_hash):
            return None
        update_last_login(db, user)
        return user
