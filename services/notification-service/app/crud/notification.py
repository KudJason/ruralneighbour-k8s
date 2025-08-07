from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate


class NotificationCRUD:
    def create(self, db: Session, obj_in: NotificationCreate) -> Notification:
        """Create a new notification"""
        # Convert enum values to strings for SQLite compatibility
        data = obj_in.model_dump()
        if data.get("notification_type"):
            data["notification_type"] = data["notification_type"].value
        if data.get("delivery_method"):
            data["delivery_method"] = data["delivery_method"].value
        if data.get("delivery_status"):
            data["delivery_status"] = data["delivery_status"].value

        # Ensure UUID fields are strings for SQLite compatibility
        if data.get("user_id"):
            data["user_id"] = str(data["user_id"])
        if data.get("related_id"):
            data["related_id"] = str(data["related_id"])

        db_obj = Notification(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, notification_id: str) -> Optional[Notification]:
        """Get a notification by ID"""
        return (
            db.query(Notification)
            .filter(Notification.notification_id == notification_id)
            .first()
        )

    def get_user_notifications(
        self, db: Session, user_id: str, skip: int = 0, limit: int = 50
    ) -> List[Notification]:
        """Get notifications for a user"""
        # Ensure user_id is a string for SQLite compatibility
        user_id_str = str(user_id)
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id_str)
            .order_by(desc(Notification.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_unread_notifications(
        self, db: Session, user_id: str, skip: int = 0, limit: int = 50
    ) -> List[Notification]:
        """Get unread notifications for a user"""
        # Ensure user_id is a string for SQLite compatibility
        user_id_str = str(user_id)
        return (
            db.query(Notification)
            .filter(
                and_(Notification.user_id == user_id_str, Notification.is_read == False)
            )
            .order_by(desc(Notification.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_unread_count(self, db: Session, user_id: str) -> int:
        """Get count of unread notifications for a user"""
        # Ensure user_id is a string for SQLite compatibility
        user_id_str = str(user_id)
        return (
            db.query(Notification)
            .filter(
                and_(Notification.user_id == user_id_str, Notification.is_read == False)
            )
            .count()
        )

    def mark_as_read(self, db: Session, notification_id: str) -> Optional[Notification]:
        """Mark a notification as read"""
        db_obj = self.get(db, notification_id)
        if not db_obj:
            return None

        db_obj.is_read = True
        db_obj.read_at = datetime.utcnow()
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def mark_all_as_read(self, db: Session, user_id: str) -> int:
        """Mark all notifications for a user as read"""
        # Ensure user_id is a string for SQLite compatibility
        user_id_str = str(user_id)
        result = (
            db.query(Notification)
            .filter(
                and_(Notification.user_id == user_id_str, Notification.is_read == False)
            )
            .update(
                {
                    Notification.is_read: True,
                    Notification.read_at: datetime.utcnow(),
                }
            )
        )
        db.commit()
        return result

    def update_delivery_status(
        self, db: Session, notification_id: str, status: str
    ) -> Optional[Notification]:
        """Update delivery status of a notification"""
        db_obj = self.get(db, notification_id)
        if not db_obj:
            return None

        db_obj.delivery_status = status
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_type(
        self,
        db: Session,
        user_id: str,
        notification_type: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Notification]:
        """Get notifications by type for a user"""
        # Ensure user_id is a string for SQLite compatibility
        user_id_str = str(user_id)
        return (
            db.query(Notification)
            .filter(
                and_(
                    Notification.user_id == user_id_str,
                    Notification.notification_type == notification_type,
                )
            )
            .order_by(desc(Notification.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def delete(self, db: Session, notification_id: str) -> bool:
        """Delete a notification"""
        db_obj = self.get(db, notification_id)
        if not db_obj:
            return False

        db.delete(db_obj)
        db.commit()
        return True

    def cleanup_old_notifications(self, db: Session, days: int = 90) -> int:
        """Delete notifications older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = (
            db.query(Notification)
            .filter(Notification.created_at < cutoff_date)
            .delete()
        )
        db.commit()
        return result


notification_crud = NotificationCRUD()
