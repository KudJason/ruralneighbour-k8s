from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.db.base import get_db
from app.api.deps import get_current_user_id
from app.schemas.service_request import (
    ServiceRequestCreate,
    ServiceRequestUpdate,
    ServiceRequestResponse,
)
from app.crud.crud_service_request import service_request_crud

router = APIRouter()


@router.post("/requests", response_model=ServiceRequestResponse)
def create_service_request(
    request: ServiceRequestCreate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create a new service request"""
    try:
        return service_request_crud.create_service_request(
            db=db, request_data=request.model_dump(), requester_id=str(current_user_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/requests", response_model=List[ServiceRequestResponse])
def list_service_requests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List service requests for the current user"""
    return service_request_crud.get_user_requests(
        db=db, requester_id=str(current_user_id), skip=skip, limit=limit
    )


@router.get("/requests/{request_id}", response_model=ServiceRequestResponse)
def get_service_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get a specific service request"""
    request = service_request_crud.get(db=db, request_id=request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Service request not found")

    # Check if user owns this request
    if request.requester_id != str(current_user_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this request"
        )

    return request


@router.put("/requests/{request_id}", response_model=ServiceRequestResponse)
def update_service_request(
    request_id: str,
    request_update: ServiceRequestUpdate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Update a service request"""
    request = service_request_crud.get(db=db, request_id=request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Service request not found")

    # Check if user owns this request
    if request.requester_id != str(current_user_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to update this request"
        )

    try:
        return service_request_crud.update_service_request(
            db=db,
            request_id=request_id,
            update_data=request_update.dict(exclude_unset=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/requests/{request_id}")
def delete_service_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Delete a service request"""
    request = service_request_crud.get(db=db, request_id=request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Service request not found")

    # Check if user owns this request
    if request.requester_id != str(current_user_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this request"
        )

    service_request_crud.remove(db=db, request_id=request_id)
    return {"message": "Service request deleted successfully"}
