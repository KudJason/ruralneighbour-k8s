from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.db.base import get_db
from app.crud.user import UserCRUD
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_my_user_info(
    current_user_id: str = "123e4567-e89b-12d3-a456-426614174000",  # Mock user ID for testing
    db: Session = Depends(get_db),
):
    """Get current user's basic information"""
    try:
        user_id = uuid.UUID(current_user_id)
        user = UserCRUD.get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format"
        )
