from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db_session, require_admin_auth
from app.services.content_service import ContentService
from app.schemas.video import VideoCreate, VideoUpdate, VideoResponse, VideoType

router = APIRouter()


@router.post("/videos", response_model=VideoResponse, tags=["admin"])
async def create_video(
    video_data: VideoCreate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Create a new video (Admin only)"""
    # Verify admin authentication
    require_admin_auth(authorization)

    video = ContentService.create_video(db, video_data)
    return video


@router.get("/videos", response_model=List[VideoResponse], tags=["public"])
async def get_videos(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)
):
    """Get all active videos (Public endpoint)"""
    videos = ContentService.get_active_videos(db, skip, limit)
    return videos


@router.get("/videos/featured", response_model=List[VideoResponse], tags=["public"])
async def get_featured_videos(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db_session)
):
    """Get featured videos (Public endpoint)"""
    videos = ContentService.get_featured_videos(db, skip, limit)
    return videos


@router.get(
    "/videos/type/{video_type}", response_model=List[VideoResponse], tags=["public"]
)
async def get_videos_by_type(
    video_type: VideoType,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_session),
):
    """Get videos by type (Public endpoint)"""
    videos = ContentService.get_videos_by_type(db, video_type.value, skip, limit)
    return videos


@router.get("/videos/{video_id}", response_model=VideoResponse, tags=["public"])
async def get_video(video_id: str, db: Session = Depends(get_db_session)):
    """Get a specific video by ID (Public endpoint)"""
    video = ContentService.get_video(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )
    return video


@router.put("/videos/{video_id}", response_model=VideoResponse, tags=["admin"])
async def update_video(
    video_id: str,
    video_data: VideoUpdate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Update a video (Admin only)"""
    # Verify admin authentication
    require_admin_auth(authorization)

    video = ContentService.update_video(db, video_id, video_data)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )
    return video


@router.delete("/videos/{video_id}", tags=["admin"])
async def delete_video(
    video_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Delete a video (Admin only)"""
    # Verify admin authentication
    require_admin_auth(authorization)

    success = ContentService.delete_video(db, video_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )
    return {"message": "Video deleted successfully"}
