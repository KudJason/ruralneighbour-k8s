from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import date, datetime
from app.models.video import Video
from app.schemas.video import VideoCreate, VideoUpdate


class VideoCRUD:
    def create(self, db: Session, obj_in: VideoCreate) -> Video:
        """Create a new video"""
        # Convert video_type enum to string for SQLite compatibility
        data = obj_in.model_dump()
        if data.get('video_type'):
            data['video_type'] = data['video_type'].value
        
        db_obj = Video(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, video_id: str) -> Optional[Video]:
        """Get a video by ID"""
        return db.query(Video).filter(Video.video_id == video_id).first()

    def get_active_videos(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[Video]:
        """Get all active videos"""
        return (
            db.query(Video)
            .filter(Video.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_featured_videos(
        self, db: Session, skip: int = 0, limit: int = 10
    ) -> List[Video]:
        """Get featured active videos"""
        return (
            db.query(Video)
            .filter(and_(Video.is_active == True, Video.is_featured == True))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_videos_by_type(
        self, db: Session, video_type: str, skip: int = 0, limit: int = 50
    ) -> List[Video]:
        """Get videos by type"""
        return (
            db.query(Video)
            .filter(and_(Video.is_active == True, Video.video_type == video_type))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(
        self, db: Session, video_id: str, obj_in: VideoUpdate
    ) -> Optional[Video]:
        """Update a video"""
        db_obj = self.get(db, video_id)
        if not db_obj:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        # Convert video_type enum to string if present
        if 'video_type' in update_data and update_data['video_type']:
            update_data['video_type'] = update_data['video_type'].value
            
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, video_id: str) -> bool:
        """Delete a video"""
        db_obj = self.get(db, video_id)
        if not db_obj:
            return False

        db.delete(db_obj)
        db.commit()
        return True

    def get_expired_videos(self, db: Session) -> List[Video]:
        """Get videos that have expired (for retention policy)"""
        today = date.today()
        return (
            db.query(Video)
            .filter(and_(Video.expiry_date.isnot(None), Video.expiry_date < today))
            .all()
        )

    def mark_as_inactive(self, db: Session, video_id: str) -> bool:
        """Mark a video as inactive instead of deleting"""
        db_obj = self.get(db, video_id)
        if not db_obj:
            return False

        db_obj.is_active = False
        db.commit()
        return True


video_crud = VideoCRUD()
