from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import uuid4
from datetime import datetime
from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_in: UserCreate, password_hash: str) -> User:
    user = User(
        user_id=uuid4(),
        email=str(user_in.email),
        password_hash=password_hash,
        full_name=str(user_in.full_name) if user_in.full_name is not None else None,
        is_active=True,
        is_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise


def update_last_login(db: Session, user: User):
    setattr(user, "last_login", datetime.utcnow())
    db.commit()
    db.refresh(user)
