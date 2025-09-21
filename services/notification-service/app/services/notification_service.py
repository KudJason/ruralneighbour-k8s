from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.notification import notification_crud
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationSummary,
)


class NotificationService:
    """Service for notification management"""

    @staticmethod
    def create_notification(
        db: Session, notification_data: NotificationCreate
    ) -> NotificationResponse:
        """Create a new notification"""
        notification = notification_crud.create(db, notification_data)
        return NotificationResponse.model_validate(notification)

    @staticmethod
    def get_notification(
        db: Session, notification_id: str
    ) -> Optional[NotificationResponse]:
        """Get a notification by ID"""
        notification = notification_crud.get(db, notification_id)
        return (
            NotificationResponse.model_validate(notification) if notification else None
        )

    @staticmethod
    def get_user_notifications(
        db: Session, user_id: str, skip: int = 0, limit: int = 50
    ) -> NotificationSummary:
        """Get notifications for a user"""
        notifications = notification_crud.get_user_notifications(
            db, user_id, skip, limit
        )
        unread_count = notification_crud.get_unread_count(db, user_id)

        return NotificationSummary(
            notifications=[
                NotificationResponse.model_validate(notif) for notif in notifications
            ],
            total_count=len(notifications),
            unread_count=unread_count,
        )

    @staticmethod
    def get_unread_notifications(
        db: Session, user_id: str, skip: int = 0, limit: int = 50
    ) -> List[NotificationResponse]:
        """Get unread notifications for a user"""
        notifications = notification_crud.get_unread_notifications(
            db, user_id, skip, limit
        )
        return [NotificationResponse.model_validate(notif) for notif in notifications]

    @staticmethod
    def get_unread_count(db: Session, user_id: str) -> int:
        """Get count of unread notifications for a user"""
        return notification_crud.get_unread_count(db, user_id)

    @staticmethod
    def mark_as_read(
        db: Session, notification_id: str
    ) -> Optional[NotificationResponse]:
        """Mark a notification as read"""
        notification = notification_crud.mark_as_read(db, notification_id)
        return (
            NotificationResponse.model_validate(notification) if notification else None
        )

    @staticmethod
    def mark_all_as_read(db: Session, user_id: str) -> int:
        """Mark all notifications for a user as read"""
        return notification_crud.mark_all_as_read(db, user_id)

    @staticmethod
    def update_delivery_status(
        db: Session, notification_id: str, status: str
    ) -> Optional[NotificationResponse]:
        """Update delivery status of a notification"""
        notification = notification_crud.update_delivery_status(
            db, notification_id, status
        )
        return (
            NotificationResponse.model_validate(notification) if notification else None
        )

    @staticmethod
    def get_by_type(
        db: Session,
        user_id: str,
        notification_type: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[NotificationResponse]:
        """Get notifications by type for a user"""
        notifications = notification_crud.get_by_type(
            db, user_id, notification_type, skip, limit
        )
        return [NotificationResponse.model_validate(notif) for notif in notifications]

    @staticmethod
    def delete_notification(db: Session, notification_id: str) -> bool:
        """Delete a notification"""
        return notification_crud.delete(db, notification_id)

    @staticmethod
    def update_notification(db: Session, notification_id: str, notification_data: NotificationUpdate) -> Optional[NotificationResponse]:
        """Update a notification"""
        notification = notification_crud.update(db, notification_id, notification_data)
        return NotificationResponse.model_validate(notification) if notification else None

    @staticmethod
    def cleanup_old_notifications(db: Session, days: int = 90) -> int:
        """Delete notifications older than specified days"""
        return notification_crud.cleanup_old_notifications(db, days)
