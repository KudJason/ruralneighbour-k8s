from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user_id
from app.schemas.service_request import (
    AvailableRequestOut,
    AvailableRequestsList,
)
from app.services.request_service import RequestService

router = APIRouter()


@router.get("/available-requests", response_model=AvailableRequestsList)
async def get_available_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get available requests for providers"""
    requests = RequestService.get_available_requests_for_provider(
        db, current_user_id, latitude, longitude, skip, limit
    )

    total = len(requests)

    return AvailableRequestsList(
        requests=requests, total=total, page=skip // limit + 1, size=limit
    )
