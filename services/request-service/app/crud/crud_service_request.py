# --- Basic CRUD class stubs for request-service ---
import uuid
from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.services.events import EventPublisher


class ServiceRequestCRUD:
    @staticmethod
    def create(db: Session, *, obj_in: Dict[str, Any], requester_id: str) -> Any:
        """Create a new service request"""
        from app.models.service_request import (
            ServiceRequest,
            ServiceType,
            ServiceRequestStatus,
        )

        # Handle both dict and Pydantic model inputs
        if hasattr(obj_in, "model_dump"):
            data = obj_in.model_dump()
        elif hasattr(obj_in, "dict"):
            data = obj_in.dict()
        else:
            data = obj_in

        request_id = str(uuid.uuid4())
        sr = ServiceRequest(
            request_id=request_id,
            requester_id=str(requester_id),  # Convert UUID to string
            title=data["title"],
            description=data.get("description"),
            service_type=ServiceType(data["service_type"]),
            pickup_latitude=data["pickup_latitude"],
            pickup_longitude=data["pickup_longitude"],
            destination_latitude=data.get("destination_latitude"),
            destination_longitude=data.get("destination_longitude"),
            offered_amount=data.get("offered_amount"),
            status=ServiceRequestStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(sr)
        db.commit()
        db.refresh(sr)

        # Publish ServiceRequestCreated event
        try:
            EventPublisher.publish_service_request_created(
                request_id=str(request_id),
                requester_id=str(requester_id),
                service_type=data["service_type"],
                location={
                    "latitude": data["pickup_latitude"],
                    "longitude": data["pickup_longitude"],
                },
                title=data.get("title"),
                offered_amount=data.get("offered_amount"),
            )
        except Exception as e:
            print(f"Failed to publish ServiceRequestCreated event: {e}")

        return sr

    @staticmethod
    def get(db: Session, request_id: str) -> Optional[Any]:
        """Get service request by ID"""
        from app.models.service_request import ServiceRequest

        return (
            db.query(ServiceRequest)
            .filter(ServiceRequest.request_id == request_id)
            .first()
        )

    @staticmethod
    def get_multi(db: Session, *, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get multiple service requests"""
        from app.models.service_request import ServiceRequest

        return db.query(ServiceRequest).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, *, db_obj: Any, obj_in: Union[Dict[str, Any], Any]) -> Any:
        """Update service request"""
        # Handle both dict and Pydantic model inputs
        if hasattr(obj_in, "model_dump"):
            update_data = obj_in.model_dump(exclude_unset=True)
        elif hasattr(obj_in, "dict"):
            update_data = obj_in.dict(exclude_unset=True)
        else:
            update_data = obj_in

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db_obj.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def remove(db: Session, *, request_id: str) -> Any:
        """Remove service request"""
        from app.models.service_request import ServiceRequest

        obj = (
            db.query(ServiceRequest)
            .filter(ServiceRequest.request_id == request_id)
            .first()
        )
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    @staticmethod
    def count_user_active_requests(db, requester_id):
        from app.models.service_request import ServiceRequest, ServiceRequestStatus

        # Count user active requests (pending, accepted, in_progress)
        return (
            db.query(ServiceRequest)
            .filter(
                ServiceRequest.requester_id == str(requester_id),
                ServiceRequest.status.in_(
                    [
                        ServiceRequestStatus.PENDING,
                        ServiceRequestStatus.ACCEPTED,
                        ServiceRequestStatus.IN_PROGRESS,
                    ]
                ),
            )
            .count()
        )

    @staticmethod
    def create_service_request(db, request_data, requester_id):
        """Create a new service request with validation"""
        from app.models.service_request import ServiceType, ServiceRequestStatus
        from app.core.config import settings

        # Check if user has too many active requests
        active_count = ServiceRequestCRUD.count_user_active_requests(db, requester_id)
        if active_count >= settings.MAX_REQUESTS_PER_USER:
            raise ValueError(f"User has too many active requests ({active_count})")

        # Validate service type
        try:
            # Handle both dict and Pydantic model inputs
            if hasattr(request_data, "model_dump"):
                data = request_data.model_dump()
            elif hasattr(request_data, "dict"):
                data = request_data.dict()
            elif hasattr(request_data, "service_type"):
                data = {"service_type": request_data.service_type}
            else:
                data = request_data

            service_type = ServiceType(data["service_type"])
        except (ValueError, KeyError):
            service_type_val = (
                data.get("service_type", "unknown")
                if isinstance(data, dict)
                else getattr(request_data, "service_type", "unknown")
            )
            raise ValueError(f"Invalid service type: {service_type_val}")

        return ServiceRequestCRUD.create(
            db=db, obj_in=request_data, requester_id=requester_id
        )

    @staticmethod
    def get_service_request(db, request_id):
        """Get service request by ID"""
        return ServiceRequestCRUD.get(db=db, request_id=request_id)

    @staticmethod
    def update_request_status(db, request_id, status):
        """Update service request status"""
        from app.models.service_request import ServiceRequestStatus

        request = ServiceRequestCRUD.get(db=db, request_id=request_id)
        if not request:
            raise ValueError("Service request not found")

        try:
            new_status = ServiceRequestStatus(status)
        except ValueError:
            raise ValueError(f"Invalid status: {status}")

        request.status = new_status
        request.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def get_available_requests(db, provider_id, skip, limit):
        """Get available requests for providers"""
        from app.models.service_request import ServiceRequest, ServiceRequestStatus

        return (
            db.query(ServiceRequest)
            .filter(
                ServiceRequest.status == ServiceRequestStatus.PENDING,
                ServiceRequest.requester_id != str(provider_id),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_user_requests(db, requester_id, skip, limit):
        """Get requests for a specific user"""
        from app.models.service_request import ServiceRequest

        return (
            db.query(ServiceRequest)
            .filter(ServiceRequest.requester_id == str(requester_id))
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update_service_request(db, request_id, update_data):
        """Update service request"""
        request = ServiceRequestCRUD.get(db=db, request_id=request_id)
        if not request:
            raise ValueError("Service request not found")

        return ServiceRequestCRUD.update(db=db, db_obj=request, obj_in=update_data)

    @staticmethod
    def update_payment_status(db, request_id, payment_status):
        """Update payment status of a service request"""
        from app.models.service_request import PaymentStatus

        request = ServiceRequestCRUD.get(db=db, request_id=request_id)
        if not request:
            raise ValueError("Service request not found")

        try:
            new_payment_status = PaymentStatus(payment_status)
        except ValueError:
            raise ValueError(f"Invalid payment status: {payment_status}")

        request.payment_status = new_payment_status
        request.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(request)
        return request


class ServiceAssignmentCRUD:
    @staticmethod
    def create_assignment(db, assignment_data, provider_id):
        """Create a new service assignment"""
        from app.models.service_request import ServiceAssignment, AssignmentStatus

        # Handle both dict and Pydantic model inputs
        if hasattr(assignment_data, "model_dump"):
            data = assignment_data.model_dump()
        elif hasattr(assignment_data, "dict"):
            data = assignment_data.dict()
        else:
            data = assignment_data

        assignment_id = str(uuid.uuid4())
        assignment = ServiceAssignment(
            assignment_id=assignment_id,
            request_id=str(data["request_id"]),
            provider_id=str(provider_id),
            status=AssignmentStatus.ASSIGNED,
            provider_notes=data.get("provider_notes"),
            estimated_completion_time=data.get("estimated_completion_time"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def get_assignment_by_request(db, request_id):
        """Get assignment by request ID"""
        from app.models.service_request import ServiceAssignment

        return (
            db.query(ServiceAssignment)
            .filter(ServiceAssignment.request_id == request_id)
            .first()
        )

    @staticmethod
    def get_assignment(db, assignment_id):
        """Get assignment by ID"""
        from app.models.service_request import ServiceAssignment

        return (
            db.query(ServiceAssignment)
            .filter(ServiceAssignment.assignment_id == str(assignment_id))
            .first()
        )

    @staticmethod
    def update_assignment(db, assignment_id, update_data):
        """Update service assignment"""
        from app.models.service_request import AssignmentStatus

        assignment = ServiceAssignmentCRUD.get_assignment(db, assignment_id)
        if not assignment:
            raise ValueError("Service assignment not found")

        # Handle both dict and Pydantic model inputs
        if hasattr(update_data, "model_dump"):
            data = update_data.model_dump(exclude_unset=True)
        elif hasattr(update_data, "dict"):
            data = update_data.dict(exclude_unset=True)
        else:
            data = update_data

        # Handle status updates
        if "status" in data:
            try:
                new_status = AssignmentStatus(data["status"])
                assignment.status = new_status

                # If completing, set completion time
                if new_status == AssignmentStatus.COMPLETED:
                    assignment.completed_at = datetime.utcnow()

                    # Publish ServiceCompleted event
                    try:
                        EventPublisher.publish_service_completed(
                            request_id=str(assignment.request_id),
                            assignment_id=str(assignment_id),
                            requester_id=(
                                str(assignment.request.requester_id)
                                if assignment.request
                                else str(assignment.provider_id)
                            ),
                            provider_id=str(assignment.provider_id),
                            completion_time=assignment.completed_at.isoformat(),
                        )
                    except Exception as e:
                        print(f"Failed to publish ServiceCompleted event: {e}")

            except ValueError:
                raise ValueError(f"Invalid assignment status: {data['status']}")

        # Update other fields
        for field, value in data.items():
            if hasattr(assignment, field) and field != "status":
                setattr(assignment, field, value)

        assignment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def get_provider_assignments(db, provider_id, skip, limit):
        """Get assignments for a provider"""
        from app.models.service_request import ServiceAssignment

        return (
            db.query(ServiceAssignment)
            .filter(ServiceAssignment.provider_id == str(provider_id))
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_active_assignments(db, provider_id):
        """Get active assignments for a provider"""
        from app.models.service_request import ServiceAssignment, AssignmentStatus

        return (
            db.query(ServiceAssignment)
            .filter(
                ServiceAssignment.provider_id == str(provider_id),
                ServiceAssignment.status.in_(
                    [
                        AssignmentStatus.ASSIGNED,
                        AssignmentStatus.ACCEPTED,
                        AssignmentStatus.IN_PROGRESS,
                    ]
                ),
            )
            .all()
        )


class RatingCRUD:
    @staticmethod
    def create_rating(db, rating_data, rater_id):
        """Create a new rating"""
        from app.models.service_request import Rating

        # Handle both dict and Pydantic model inputs
        if hasattr(rating_data, "model_dump"):
            data = rating_data.model_dump()
        elif hasattr(rating_data, "dict"):
            data = rating_data.dict()
        else:
            data = rating_data

        # Check if rating already exists
        existing_rating = RatingCRUD.check_existing_rating(
            db,
            data["assignment_id"],
            rater_id,
            data["is_provider_rating"],
        )
        if existing_rating:
            raise ValueError("Rating already exists for this assignment and rater")

        rating_id = str(uuid.uuid4())
        rating = Rating(
            rating_id=rating_id,
            assignment_id=str(data["assignment_id"]),
            rater_id=str(rater_id),
            ratee_id=str(data["ratee_id"]),
            rating_score=data["rating_score"],
            review_text=data.get("review_text"),
            is_provider_rating=1 if data["is_provider_rating"] else 0,
            created_at=datetime.utcnow(),
        )
        db.add(rating)
        db.commit()
        db.refresh(rating)

        # Publish RatingCreated event
        try:
            EventPublisher.publish_rating_created(
                rating_id=str(rating_id),
                assignment_id=str(data["assignment_id"]),
                rater_id=str(rater_id),
                ratee_id=str(data["ratee_id"]),
                rating_score=data["rating_score"],
            )
        except Exception as e:
            print(f"Failed to publish RatingCreated event: {e}")

        return rating

    @staticmethod
    def check_existing_rating(db, assignment_id, rater_id, is_provider_rating):
        """Check if rating already exists"""
        from app.models.service_request import Rating

        return (
            db.query(Rating)
            .filter(
                Rating.assignment_id == str(assignment_id),
                Rating.rater_id == str(rater_id),
                Rating.is_provider_rating == (1 if is_provider_rating else 0),
            )
            .first()
        )

    @staticmethod
    def get_rating(db, rating_id):
        """Get rating by ID"""
        from app.models.service_request import Rating

        return db.query(Rating).filter(Rating.rating_id == rating_id).first()

    @staticmethod
    def get_user_ratings_received(db, user_id, skip, limit):
        """Get ratings received by a user"""
        from app.models.service_request import Rating

        return (
            db.query(Rating)
            .filter(Rating.ratee_id == str(user_id))
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_assignment_ratings(db, assignment_id):
        """Get all ratings for an assignment"""
        from app.models.service_request import Rating

        return db.query(Rating).filter(Rating.assignment_id == str(assignment_id)).all()

    @staticmethod
    def calculate_average_rating(db, user_id):
        """Calculate average rating for a user"""
        from app.models.service_request import Rating
        from sqlalchemy import func

        result = (
            db.query(func.avg(Rating.rating_score))
            .filter(Rating.ratee_id == str(user_id))
            .scalar()
        )
        return float(result) if result else 0.0


# Create instances for easy import
service_request_crud = ServiceRequestCRUD()
service_assignment_crud = ServiceAssignmentCRUD()
rating_crud = RatingCRUD()
