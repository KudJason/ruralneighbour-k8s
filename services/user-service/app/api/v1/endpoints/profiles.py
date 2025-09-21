from fastapi import APIRouter, Depends, HTTPException, status, Body
import json
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.db.base import get_db
from app.crud.profile import ProfileCRUD
from app.crud.user import UserCRUD
from app.schemas.profile import (
    UserProfileResponse,
    UserProfileUpdate,
    ProviderProfileResponse,
    ProviderProfileCreate,
    ProviderProfileUpdate,
    ModeSwitch,
)
# 移除手动映射函数，现在使用Pydantic的alias功能


router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user_id: str = "123e4567-e89b-12d3-a456-426614174000",
    db: Session = Depends(get_db),
):
    """Get current user's profile"""
    try:
        user_id = uuid.UUID(current_user_id)
        profile = ProfileCRUD.get_user_profile(db, user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        return profile
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format"
        )


# 移除手动映射函数，现在使用Pydantic的alias功能


@router.patch("/me", response_model=UserProfileResponse)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user_id: str = "123e4567-e89b-12d3-a456-426614174000",
    db: Session = Depends(get_db),
):
    """Update current user's profile with automatic field mapping."""
    try:
        user_id = uuid.UUID(current_user_id)
        updated_profile = ProfileCRUD.update_user_profile(db, user_id, profile_update)
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        return updated_profile
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format"
        )


@router.patch("/mode", response_model=UserProfileResponse)
async def switch_user_mode(
    mode_switch: ModeSwitch,
    current_user_id: str = "123e4567-e89b-12d3-a456-426614174000",
    db: Session = Depends(get_db),
):
    """Switch user's default mode between NIN and LAH"""
    try:
        user_id = uuid.UUID(current_user_id)
        updated_user = UserCRUD.update_user_mode(db, user_id, mode_switch.default_mode)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        profile_update = UserProfileUpdate(default_mode=mode_switch.default_mode)
        updated_profile = ProfileCRUD.update_user_profile(db, user_id, profile_update)
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        return updated_profile
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format"
        )


@router.get("/provider", response_model=Optional[ProviderProfileResponse])
async def get_my_provider_profile(
    current_user_id: str = "123e4567-e89b-12d3-a456-426614174000",
    db: Session = Depends(get_db),
):
    """Get current user's provider profile"""
    try:
        user_id = uuid.UUID(current_user_id)
        provider_profile = ProfileCRUD.get_provider_profile(db, user_id)
        return provider_profile
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format"
        )


@router.post("/provider", response_model=ProviderProfileResponse)
async def create_provider_profile(
    provider_data: ProviderProfileCreate,
    current_user_id: str = "123e4567-e89b-12d3-a456-426614174000",
    db: Session = Depends(get_db),
):
    """Create provider profile for current user"""
    try:
        user_id = uuid.UUID(current_user_id)
        existing_profile = ProfileCRUD.get_provider_profile(db, user_id)
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provider profile already exists",
            )
        provider_data.user_id = user_id
        provider_profile = ProfileCRUD.create_provider_profile(db, provider_data)
        return provider_profile
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format"
        )


@router.patch("/provider", response_model=ProviderProfileResponse)
async def update_provider_profile(
    provider_update: ProviderProfileUpdate,
    current_user_id: str = "123e4567-e89b-12d3-a456-426614174000",
    db: Session = Depends(get_db),
):
    """Update current user's provider profile with automatic field mapping.

    Automatic field mapping:
    - services -> services_offered (JSON string)
    - availability -> availability_schedule
    - description -> vehicle_description
    """
    try:
        user_id = uuid.UUID(current_user_id)
        updated_profile = ProfileCRUD.update_provider_profile(
            db, user_id, provider_update
        )
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider profile not found",
            )
        return updated_profile
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format"
        )
