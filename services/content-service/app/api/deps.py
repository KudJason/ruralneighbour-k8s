from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.core.config import settings
import httpx


def get_db_session() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    return get_db()


def verify_admin_token(token: str) -> bool:
    """Verify admin token - placeholder for actual JWT verification"""
    # In a real implementation, this would verify JWT tokens
    # For now, we'll use a simple check
    return token == "admin-token"


def get_current_admin_user(token: str = None) -> Optional[str]:
    """Get current admin user from token"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    if not verify_admin_token(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    return "admin"  # In real implementation, this would be the user ID


def require_admin_auth(token: str = None) -> str:
    """Require admin authentication"""
    return get_current_admin_user(token)
