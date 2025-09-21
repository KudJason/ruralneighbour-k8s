from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user_id
from app.schemas.service_request import (
    AvailableRequestOut,
    AvailableRequestsList,
    ServiceAssignmentCreate,
    ServiceAssignmentOut,
    StatusUpdateRequest,
)
from app.services.request_service import RequestService
from app.crud.crud_service_request import ServiceAssignmentCRUD, ServiceRequestCRUD

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


@router.post("/requests/{request_id}/accept", response_model=ServiceAssignmentOut, status_code=status.HTTP_201_CREATED)
async def accept_request(
    request_id: str,
    body: dict = Body(None),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Accept a request as provider. Maps notes -> provider_notes."""
    notes = (body or {}).get("notes")
    assignment_in = ServiceAssignmentCreate(
        request_id=str(request_id),
        provider_notes=notes,
        estimated_completion_time=None,
    )
    assignment = RequestService.assign_provider_to_request(
        db, uuid.UUID(request_id), current_user_id, assignment_in
    )
    return assignment


@router.patch("/requests/{request_id}/status", response_model=ServiceAssignmentOut)
async def update_request_status(
    request_id: str,
    body: dict = Body(...),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update assignment status. Maps progress_notes -> notes. Auto completed_at handled in CRUD."""
    # Find assignment by request
    assignment = ServiceAssignmentCRUD.get_assignment_by_request(db, request_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No assignment for this request")

    status_value = (body or {}).get("status")
    notes_value = (body or {}).get("progress_notes") or (body or {}).get("notes")
    status_update = StatusUpdateRequest(status=status_value, notes=notes_value)

    updated = RequestService.update_assignment_status(
        db, uuid.UUID(str(assignment.assignment_id)), status_update, current_user_id
    )
    return updated
