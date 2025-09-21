from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
import uuid

from app.db.base import get_db
from app.crud.user import UserCRUD
from app.crud.profile import ProfileCRUD
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.profile import UserProfileUpdate

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


@router.patch("/me", response_model=UserResponse)
async def patch_my_user_info(
    user_update: UserUpdate,
    current_user_id: str = "123e4567-e89b-12d3-a456-426614174000",
    db: Session = Depends(get_db),
):
    """Patch current user's basic info with automatic field mapping.

    Automatic field mapping:
    - fullName -> full_name
    - phone -> phone_number (delegated to profile update)
    """
    try:
        user_id = uuid.UUID(current_user_id)

        # Update user fields
        updated_user = None
        if any([user_update.full_name is not None, user_update.default_mode is not None]):
            updated_user = UserCRUD.update_user(db, user_id, user_update)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )
        else:
            # No user fields to update; fetch for response consistency if exists
            updated_user = UserCRUD.get_user(db, user_id)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

        # Delegate phone update to profile if present
        if user_update.phone_number is not None:
            profile_update = UserProfileUpdate(phone_number=user_update.phone_number)
            ProfileCRUD.update_user_profile(db, user_id, profile_update)

        return updated_user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format"
        )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Create a user; requires password.

    Accept alias fields: fullName -> full_name.
    """
    email = body.get("email")
    password = body.get("password")
    if not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing required field: password",
        )
    if not email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing required field: email",
        )
    full_name = body.get("full_name", body.get("fullName"))
    default_mode = body.get("default_mode")
    is_active = body.get("is_active")

    user = UserCRUD.create_user(
        db,
        email=email,
        password=password,
        full_name=full_name,
        default_mode=default_mode,
        is_active=is_active,
    )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    try:
        uid = uuid.UUID(user_id)
        full_name = body.get("full_name", body.get("fullName"))
        default_mode = body.get("default_mode")
        is_active = body.get("is_active")
        user_update = UserUpdate()
        if full_name is not None:
            user_update.full_name = full_name
        if default_mode is not None:
            user_update.default_mode = default_mode
        if is_active is not None:
            user_update.is_active = bool(is_active)

        updated = UserCRUD.update_user(db, uid, user_update)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        return updated
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
