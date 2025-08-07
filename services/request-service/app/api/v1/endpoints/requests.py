from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.schemas.service_request import (
    ServiceRequestCreate,
    ServiceRequestUpdate,
    ServiceRequestOut,
    ServiceRequestList,
    ServiceAssignmentCreate,
    ServiceAssignmentOut,
    ServiceAssignmentUpdate,
    RatingCreate,
    RatingOut,
    StatusUpdateRequest,
    MessageResponse,
)
from app.services.request_service import RequestService
from app.crud.crud_service_request import (
    ServiceRequestCRUD,
    ServiceAssignmentCRUD,
    RatingCRUD,
)
from app.models.service_request import Rating
from app.api.deps import get_current_user_id

router = APIRouter()


@router.post("/", response_model=ServiceRequestOut, status_code=status.HTTP_201_CREATED)
def create_service_request(
    request_data: ServiceRequestCreate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Create a new service request.

    - **NIN users** can create service requests
    - Validates maximum active requests per user
    - Publishes ServiceRequestCreated event
    """
    service_request = RequestService.create_service_request(
        db, request_data, current_user_id
    )
    return service_request


@router.get("/", response_model=ServiceRequestList)
def get_user_service_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Get all service requests for the current user.

    - Returns requests created by the current user
    - Supports pagination
    """
    requests = ServiceRequestCRUD.get_user_requests(db, current_user_id, skip, limit)
    total = len(requests) + skip  # Simplified count for pagination

    return ServiceRequestList(
        requests=requests, total=total, page=skip // limit + 1, size=len(requests)
    )


@router.get("/{request_id}", response_model=ServiceRequestOut)
def get_service_request(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Get a specific service request by ID.

    - Only the requester can view their own requests
    - Returns 404 if request not found or not owned by user
    """
    service_request = ServiceRequestCRUD.get_service_request(db, request_id)

    if not service_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found"
        )

    if service_request.requester_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this request",
        )

    return service_request


@router.put("/{request_id}", response_model=ServiceRequestOut)
def update_service_request(
    request_id: uuid.UUID,
    update_data: ServiceRequestUpdate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Update a service request.

    - Only the requester can update their own requests
    - Cannot update requests that are no longer pending
    """
    # First check if request exists and belongs to user
    service_request = ServiceRequestCRUD.get_service_request(db, request_id)

    if not service_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found"
        )

    if service_request.requester_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this request",
        )

    if service_request.status.value != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update request that is no longer pending",
        )

    updated_request = ServiceRequestCRUD.update_service_request(
        db, request_id, update_data
    )

    if not updated_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to update service request",
        )

    return updated_request


@router.delete("/{request_id}", response_model=MessageResponse)
def delete_service_request(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Delete a service request (soft delete).

    - Only the requester can delete their own requests
    - Cannot delete requests that are no longer pending
    """
    success = ServiceRequestCRUD.delete_service_request(db, request_id, current_user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found or cannot be deleted",
        )

    return MessageResponse(message="Service request deleted successfully")


@router.post(
    "/{request_id}/assign",
    response_model=ServiceAssignmentOut,
    status_code=status.HTTP_201_CREATED,
)
def assign_provider_to_request(
    request_id: uuid.UUID,
    assignment_data: ServiceAssignmentCreate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Assign current user (LAH provider) to a service request.

    - **LAH users** can assign themselves to pending requests
    - Cannot assign to own requests
    - Updates request status to 'accepted'
    - Publishes status change events
    """
    # Ensure the request_id in path matches the one in body
    assignment_data.request_id = request_id

    assignment = RequestService.assign_provider_to_request(
        db, request_id, current_user_id, assignment_data
    )
    return assignment


@router.get("/{request_id}/assignment", response_model=ServiceAssignmentOut)
def get_request_assignment(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Get the assignment for a specific request.

    - Requester and provider can view the assignment
    """
    service_request = ServiceRequestCRUD.get_service_request(db, request_id)
    if not service_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found"
        )

    assignment = ServiceAssignmentCRUD.get_assignment_by_request(db, request_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assignment found for this request",
        )

    # Check if user is authorized to view
    if (
        current_user_id != service_request.requester_id
        and current_user_id != assignment.provider_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this assignment",
        )

    return assignment


@router.put(
    "/{request_id}/assignment/{assignment_id}/status",
    response_model=ServiceAssignmentOut,
)
def update_assignment_status(
    request_id: uuid.UUID,
    assignment_id: uuid.UUID,
    status_data: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Update assignment status.

    - Provider and requester can update assignment status
    - Validates status transitions
    - Publishes appropriate events
    """
    assignment = RequestService.update_assignment_status(
        db, assignment_id, status_data, current_user_id
    )
    return assignment


@router.post(
    "/{request_id}/assignment/{assignment_id}/rating",
    response_model=RatingOut,
    status_code=status.HTTP_201_CREATED,
)
def create_rating(
    request_id: uuid.UUID,
    assignment_id: uuid.UUID,
    rating_data: RatingCreate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Create a rating for a completed service.

    - Only available after service completion
    - Requester can rate provider, provider can rate requester
    - Publishes RatingCreated event
    """
    # Ensure assignment_id matches
    rating_data.assignment_id = assignment_id

    rating = RequestService.create_rating(db, rating_data, current_user_id)
    return rating


@router.get("/{request_id}/ratings", response_model=List[RatingOut])
def get_request_ratings(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Get all ratings for a specific request.

    - Requester and provider can view ratings
    """
    service_request = ServiceRequestCRUD.get_service_request(db, request_id)
    if not service_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found"
        )

    assignment = ServiceAssignmentCRUD.get_assignment_by_request(db, request_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assignment found for this request",
        )

    # Check authorization
    if (
        current_user_id != service_request.requester_id
        and current_user_id != assignment.provider_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view ratings for this request",
        )

    # Get ratings by assignment
    ratings = (
        db.query(Rating).filter(Rating.assignment_id == assignment.assignment_id).all()
    )
    return ratings
