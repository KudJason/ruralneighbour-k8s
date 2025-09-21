from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.deps import get_db_session, require_admin_auth
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationSummary,
)

router = APIRouter()


@router.post(
    "/notifications", response_model=NotificationResponse, tags=["notifications"]
)
async def create_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Create a new notification"""
    # Verify authentication
    require_admin_auth(authorization)

    notification = NotificationService.create_notification(db, notification_data)
    return notification


@router.get(
    "/notifications/{notification_id}",
    response_model=NotificationResponse,
    tags=["notifications"],
)
async def get_notification(
    notification_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get a specific notification by ID"""
    # Verify authentication
    require_admin_auth(authorization)

    notification = NotificationService.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    return notification


@router.get(
    "/notifications/user/{user_id}",
    response_model=NotificationSummary,
    tags=["notifications"],
)
async def get_user_notifications(
    user_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get notifications for a user"""
    # Verify authentication
    require_admin_auth(authorization)

    notifications = NotificationService.get_user_notifications(db, user_id, skip, limit)
    return notifications


@router.get(
    "/notifications/user/{user_id}/unread",
    response_model=List[NotificationResponse],
    tags=["notifications"],
)
async def get_unread_notifications(
    user_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get unread notifications for a user"""
    # Verify authentication
    require_admin_auth(authorization)

    notifications = NotificationService.get_unread_notifications(
        db, user_id, skip, limit
    )
    return notifications


@router.get("/notifications/unread/{user_id}", tags=["notifications"])
async def get_unread_count(
    user_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get count of unread notifications for a user"""
    # Verify authentication
    require_admin_auth(authorization)

    count = NotificationService.get_unread_count(db, user_id)
    return {"unread_count": count}


@router.put(
    "/notifications/{notification_id}/read",
    response_model=NotificationResponse,
    tags=["notifications"],
)
async def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Mark a notification as read"""
    # Verify authentication
    require_admin_auth(authorization)

    notification = NotificationService.mark_as_read(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    return notification


@router.put("/notifications/user/{user_id}/read-all", tags=["notifications"])
async def mark_all_notifications_as_read(
    user_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Mark all notifications for a user as read"""
    # Verify authentication
    require_admin_auth(authorization)

    count = NotificationService.mark_all_as_read(db, user_id)
    return {"notifications_marked_read": count}


@router.put(
    "/notifications/{notification_id}/status",
    response_model=NotificationResponse,
    tags=["notifications"],
)
async def update_delivery_status(
    notification_id: str,
    status: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Update delivery status of a notification"""
    # Verify authentication
    require_admin_auth(authorization)

    notification = NotificationService.update_delivery_status(
        db, notification_id, status
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    return notification


@router.get(
    "/notifications/user/{user_id}/type/{notification_type}",
    response_model=List[NotificationResponse],
    tags=["notifications"],
)
async def get_notifications_by_type(
    user_id: str,
    notification_type: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get notifications by type for a user"""
    # Verify authentication
    require_admin_auth(authorization)

    notifications = NotificationService.get_by_type(
        db, user_id, notification_type, skip, limit
    )
    return notifications


@router.delete("/notifications/{notification_id}", tags=["notifications"])
async def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Delete a notification"""
    # Verify authentication
    require_admin_auth(authorization)

    success = NotificationService.delete_notification(db, notification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    return {"message": "Notification deleted successfully"}


@router.patch("/notifications/{notification_id}", response_model=NotificationResponse, tags=["notifications"])
async def update_notification(
    notification_id: str,
    notification_data: NotificationUpdate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Update a notification"""
    # Verify authentication
    require_admin_auth(authorization)

    notification = NotificationService.update_notification(db, notification_id, notification_data)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    return notification


@router.delete("/notifications/cleanup", tags=["notifications"])
async def cleanup_old_notifications(
    days: int = 90,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Delete notifications older than specified days"""
    # Verify authentication
    require_admin_auth(authorization)

    count = NotificationService.cleanup_old_notifications(db, days)
    return {"notifications_deleted": count}


# ========== Frontend Compatibility Endpoints ==========

@router.post("/notifications/mark_all_read", tags=["notifications"])
async def mark_all_notifications_read_for_frontend(
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Mark all notifications as read for current user (frontend compatibility)"""
    # Verify authentication
    require_admin_auth(authorization)
    
    # In a real implementation, you'd get the current user ID
    current_user_id = "123e4567-e89b-12d3-a456-426614174000"  # Mock user ID
    count = NotificationService.mark_all_as_read(db, current_user_id)
    return {"notifications_marked_read": count}


@router.get("/notifications/unread/count", tags=["notifications"])
async def get_unread_notification_count_for_frontend(
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get unread notification count for current user (frontend compatibility)"""
    # Verify authentication
    require_admin_auth(authorization)
    
    # In a real implementation, you'd get the current user ID
    current_user_id = "123e4567-e89b-12d3-a456-426614174000"  # Mock user ID
    count = NotificationService.get_unread_count(db, current_user_id)
    return {"unread_count": count}

