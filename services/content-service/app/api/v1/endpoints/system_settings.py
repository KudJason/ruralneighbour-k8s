from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.api.deps import get_db_session, require_admin_auth
from app.services.content_service import ContentService
from app.schemas.system_setting import (
    SystemSettingCreate,
    SystemSettingUpdate,
    SystemSettingResponse,
)

router = APIRouter()


@router.post("/system/settings", response_model=SystemSettingResponse, tags=["admin"])
async def create_system_setting(
    setting_data: SystemSettingCreate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Create a new system setting (Admin only)"""
    # Verify admin authentication
    require_admin_auth(authorization)

    setting = ContentService.create_system_setting(db, setting_data)
    return setting


@router.get(
    "/system/settings", response_model=List[SystemSettingResponse], tags=["admin"]
)
async def get_all_system_settings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get all system settings (Admin only)"""
    # Verify admin authentication
    require_admin_auth(authorization)

    settings = ContentService.get_all_system_settings(db, skip, limit)
    return settings


@router.get(
    "/system/settings/{setting_id}",
    response_model=SystemSettingResponse,
    tags=["admin"],
)
async def get_system_setting(
    setting_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get a specific system setting by ID (Admin only)"""
    # Verify admin authentication
    require_admin_auth(authorization)

    setting = ContentService.get_system_setting(db, setting_id)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="System setting not found"
        )
    return setting


@router.get(
    "/system/settings/key/{setting_key}",
    response_model=SystemSettingResponse,
    tags=["admin"],
)
async def get_system_setting_by_key(
    setting_key: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get a system setting by key (Admin only)"""
    # Verify admin authentication
    require_admin_auth(authorization)

    setting = ContentService.get_system_setting_by_key(db, setting_key)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="System setting not found"
        )
    return setting


@router.put(
    "/system/settings/{setting_id}",
    response_model=SystemSettingResponse,
    tags=["admin"],
)
async def update_system_setting(
    setting_id: str,
    setting_data: SystemSettingUpdate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Update a system setting (Admin only)"""
    # Verify admin authentication
    require_admin_auth(authorization)

    setting = ContentService.update_system_setting(db, setting_id, setting_data)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="System setting not found"
        )
    return setting


@router.put(
    "/system/settings/key/{setting_key}",
    response_model=SystemSettingResponse,
    tags=["admin"],
)
async def update_system_setting_by_key(
    setting_key: str,
    setting_data: SystemSettingUpdate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Update a system setting by key (Admin only)"""
    # Verify admin authentication
    require_admin_auth(authorization)

    setting = ContentService.update_system_setting_by_key(db, setting_key, setting_data)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="System setting not found"
        )
    return setting


@router.delete("/system/settings/{setting_id}", tags=["admin"])
async def delete_system_setting(
    setting_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Delete a system setting (Admin only)"""
    # Verify admin authentication
    require_admin_auth(authorization)

    success = ContentService.delete_system_setting(db, setting_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="System setting not found"
        )
    return {"message": "System setting deleted successfully"}
