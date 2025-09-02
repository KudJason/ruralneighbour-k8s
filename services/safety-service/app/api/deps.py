from typing import Optional

from app.db.base import get_db
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


def get_db_session() -> Session:
    return next(get_db())


def verify_user_token(token: Optional[str]) -> bool:
    if not token:
        return False
    return token.startswith("user_") or token.startswith("admin_")


def verify_admin_token(token: Optional[str]) -> bool:
    if not token:
        return False
    return token.startswith("admin_")


def require_auth(token: Optional[str] = None) -> str:
    if not token or not verify_user_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return "user"


def require_admin_auth(token: Optional[str] = None) -> str:
    if not token or not verify_admin_token(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return "admin"


