from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from decimal import Decimal

from app.models.service_request import (
    ServiceRequest,
    ServiceAssignment,
    Rating,
    ServiceRequestStatus,
    AssignmentStatus,
)
from app.schemas.service_request import (
    ServiceRequestCreate,
    ServiceRequestUpdate,
    ServiceAssignmentCreate,
    ServiceAssignmentUpdate,
    RatingCreate,
    StatusUpdateRequest,
)
from app.crud.crud_service_request import (
    ServiceRequestCRUD,
    ServiceAssignmentCRUD,
    RatingCRUD,
)
from app.services.events import EventPublisher
from app.core.config import MAX_REQUESTS_PER_USER, SERVICE_RADIUS_MILES
from fastapi import HTTPException, status


class RequestService:
    """Main business logic for service request management"""

    @staticmethod
    def create_service_request(
        db: Session, request_data: ServiceRequestCreate, requester_id: uuid.UUID
    ) -> ServiceRequest:
        """Create a new service request with business logic validation"""

        # Check if user has too many active requests
        active_count = ServiceRequestCRUD.count_user_active_requests(db, requester_id)
        if active_count >= MAX_REQUESTS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {MAX_REQUESTS_PER_USER} active requests allowed",
            )

        # Create the request
        service_request = ServiceRequestCRUD.create_service_request(
            db, request_data, requester_id
        )

        return service_request

    @staticmethod
    def assign_provider_to_request(
        db: Session,
        request_id: uuid.UUID,
        provider_id: uuid.UUID,
        assignment_data: ServiceAssignmentCreate,
    ) -> ServiceAssignment:
        """Assign a provider to a service request"""

        # Get the request
        service_request = ServiceRequestCRUD.get_service_request(db, request_id)
        if not service_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service request not found",
            )

        # Check if request is available
        if service_request.status != ServiceRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service request is no longer available",
            )

        # Check if provider is trying to assign to their own request
        if service_request.requester_id == str(provider_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign to your own request",
            )

        # Check if assignment already exists
        existing_assignment = ServiceAssignmentCRUD.get_assignment_by_request(
            db, request_id
        )
        if existing_assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request already has an assignment",
            )

        # Create assignment
        assignment = ServiceAssignmentCRUD.create_assignment(
            db, assignment_data, provider_id
        )

        # Update request status to accepted
        ServiceRequestCRUD.update_request_status(
            db, request_id, ServiceRequestStatus.ACCEPTED
        )

        # Publish status change event
        try:
            EventPublisher.publish_request_status_changed(
                request_id=str(request_id),
                old_status="pending",
                new_status="accepted",
                requester_id=str(service_request.requester_id),
                provider_id=str(provider_id),
            )
        except Exception as e:
            print(f"Failed to publish status change event: {e}")

        return assignment

    @staticmethod
    def update_assignment_status(
        db: Session,
        assignment_id: uuid.UUID,
        status_data: StatusUpdateRequest,
        user_id: uuid.UUID,
    ) -> ServiceAssignment:
        """Update assignment status with business logic"""

        assignment = ServiceAssignmentCRUD.get_assignment(db, assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
            )

        # Get the service request
        service_request = ServiceRequestCRUD.get_service_request(
            db, assignment.request_id
        )
        if not service_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service request not found",
            )

        # Check permissions - only provider or requester can update
        if (
            str(user_id) != assignment.provider_id
            and str(user_id) != service_request.requester_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this assignment",
            )

        # Validate status transitions
        current_status = assignment.status.value
        new_status = status_data.status

        valid_transitions = {
            "assigned": ["accepted", "cancelled"],
            "accepted": ["in_progress", "cancelled"],
            "in_progress": ["completed", "cancelled"],
            "completed": [],
            "cancelled": [],
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {current_status} to {new_status}",
            )

        # Update assignment
        update_data = ServiceAssignmentUpdate(
            status=new_status,
            provider_notes=status_data.notes,
            estimated_completion_time=None,
            completion_notes=None,
        )
        assignment = ServiceAssignmentCRUD.update_assignment(
            db, assignment_id, update_data
        )

        # Update request status accordingly
        request_status_map = {
            "accepted": ServiceRequestStatus.ACCEPTED,
            "in_progress": ServiceRequestStatus.IN_PROGRESS,
            "completed": ServiceRequestStatus.COMPLETED,
            "cancelled": ServiceRequestStatus.CANCELLED,
        }

        if new_status in request_status_map:
            ServiceRequestCRUD.update_request_status(
                db, assignment.request_id, request_status_map[new_status]
            )

        # Publish events
        try:
            EventPublisher.publish_request_status_changed(
                request_id=str(assignment.request_id),
                old_status=current_status,
                new_status=new_status,
                requester_id=str(service_request.requester_id),
                provider_id=str(assignment.provider_id),
            )

            # If completed, publish ServiceCompleted event
            if new_status == "completed":
                EventPublisher.publish_service_completed(
                    request_id=str(assignment.request_id),
                    assignment_id=str(assignment.assignment_id),
                    requester_id=str(service_request.requester_id),
                    provider_id=str(assignment.provider_id),
                    completion_time=(
                        assignment.completed_at.isoformat()
                        if assignment.completed_at
                        else None
                    ),
                )
        except Exception as e:
            print(f"Failed to publish events: {e}")

        return assignment

    @staticmethod
    def create_rating(
        db: Session, rating_data: RatingCreate, rater_id: uuid.UUID
    ) -> Rating:
        """Create a rating with validation"""

        # Get assignment
        assignment = ServiceAssignmentCRUD.get_assignment(db, rating_data.assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
            )

        # Get service request
        service_request = ServiceRequestCRUD.get_service_request(
            db, assignment.request_id
        )
        if not service_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service request not found",
            )

        # Check if assignment is completed
        if assignment.status != AssignmentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only rate completed services",
            )

        # Validate rater permissions
        if rating_data.is_provider_rating:
            # Rating the provider - rater must be the requester
            if str(rater_id) != service_request.requester_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the requester can rate the provider",
                )
            if rating_data.ratee_id != assignment.provider_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid ratee_id for provider rating",
                )
        else:
            # Rating the requester - rater must be the provider
            if str(rater_id) != assignment.provider_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the provider can rate the requester",
                )
            if rating_data.ratee_id != service_request.requester_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid ratee_id for requester rating",
                )

        # Check if rating already exists
        existing_rating = RatingCRUD.check_existing_rating(
            db, rating_data.assignment_id, rater_id, rating_data.is_provider_rating
        )
        if existing_rating:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating already exists for this assignment",
            )

        # Create rating
        rating = RatingCRUD.create_rating(db, rating_data, rater_id)

        return rating

    @staticmethod
    def get_available_requests_for_provider(
        db: Session,
        provider_id: uuid.UUID,
        provider_lat: Optional[float] = None,
        provider_lng: Optional[float] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ServiceRequest]:
        """Get available requests for a provider with optional distance filtering"""

        available_requests = ServiceRequestCRUD.get_available_requests(
            db, provider_id, skip, limit
        )

        # If provider location is provided, calculate distances and filter by service radius
        if provider_lat is not None and provider_lng is not None:
            filtered_requests = []
            for request in available_requests:
                distance = RequestService._calculate_distance(
                    provider_lat,
                    provider_lng,
                    float(request.pickup_latitude),
                    float(request.pickup_longitude),
                )

                if distance <= SERVICE_RADIUS_MILES:
                    # Add distance to the request object (for display purposes)
                    request.distance_miles = Decimal(str(round(distance, 2)))
                    filtered_requests.append(request)

            return filtered_requests

        return available_requests

    @staticmethod
    def _calculate_distance(
        lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points using Haversine formula"""
        import math

        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        # Radius of earth in miles
        r = 3956

        return c * r
