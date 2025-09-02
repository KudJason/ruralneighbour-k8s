# --- Basic CRUD class stubs for request-service ---
import uuid
from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from sqlalchemy import func


class ServiceRequestCRUD:
    @staticmethod
    def create(db: Session, *, obj_in: Dict[str, Any]) -> Any:
        """Create a new service request"""
        from app.models.service_request import (
            ServiceRequest,
            ServiceType,
            ServiceRequestStatus,
        )
        import datetime
        data = obj_in if isinstance(obj_in, dict) else getattr(obj_in, 'dict', lambda: {})()
        sr = ServiceRequest(
            request_id=str(uuid.uuid4()),
            requester_id=str(data.get('requester_id', 'default-user')),
            title=data['title'],
            description=data.get('description'),
            service_type=ServiceType(data['service_type']),
            pickup_latitude=data['pickup_latitude'],
            pickup_longitude=data['pickup_longitude'],
            destination_latitude=data.get('destination_latitude'),
            destination_longitude=data.get('destination_longitude'),
            offered_amount=data.get('offered_amount'),
            status=ServiceRequestStatus.PENDING,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        db.add(sr)
        db.commit()
        db.refresh(sr)
        return sr

    @staticmethod
    def get(db: Session, request_id: str) -> Optional[Any]:
        """Get service request by ID"""
        from app.models.service_request import ServiceRequest
        return db.query(ServiceRequest).filter(ServiceRequest.request_id == str(request_id)).first()

    @staticmethod
    def get_multi(db: Session, *, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get multiple service requests"""
        from app.models.service_request import ServiceRequest
        return db.query(ServiceRequest).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, *, db_obj: Any, obj_in: Union[Dict[str, Any], Any]) -> Any:
        """Update service request"""
        import datetime
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = getattr(obj_in, 'dict', lambda **kwargs: {})(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db_obj.updated_at = datetime.datetime.utcnow()
        db.commit(); db.refresh(db_obj)
        return db_obj

    @staticmethod
    def remove(db: Session, request_id: str) -> Any:
        """Remove service request"""
        from app.models.service_request import ServiceRequest
        obj = db.query(ServiceRequest).filter(ServiceRequest.request_id == str(request_id)).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    @staticmethod
    def count_user_active_requests(db, requester_id):
        from app.models.service_request import ServiceRequest, ServiceRequestStatus
        return (
            db.query(ServiceRequest)
            .filter(
                ServiceRequest.requester_id == str(requester_id),
                ServiceRequest.status.in_([
                    ServiceRequestStatus.PENDING,
                    ServiceRequestStatus.ACCEPTED,
                    ServiceRequestStatus.IN_PROGRESS,
                ]),
            ).count()
        )

    @staticmethod
    def create_service_request(db, request_data, requester_id):
        from app.models.service_request import (
            ServiceRequest,
            ServiceType,
            ServiceRequestStatus,
        )
        import datetime
        sr = ServiceRequest(
            request_id=str(uuid.uuid4()),
            requester_id=str(requester_id),
            title=request_data.title,
            description=getattr(request_data, 'description', None),
            service_type=ServiceType(request_data.service_type),
            pickup_latitude=request_data.pickup_latitude,
            pickup_longitude=request_data.pickup_longitude,
            destination_latitude=getattr(request_data, 'destination_latitude', None),
            destination_longitude=getattr(request_data, 'destination_longitude', None),
            offered_amount=getattr(request_data, 'offered_amount', None),
            status=ServiceRequestStatus.PENDING,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        db.add(sr); db.commit(); db.refresh(sr); return sr

    @staticmethod
    def get_service_request(db, request_id):
        from app.models.service_request import ServiceRequest
        return db.query(ServiceRequest).filter(ServiceRequest.request_id == str(request_id)).first()

    @staticmethod
    def update_request_status(db, request_id, status):
        from app.models.service_request import ServiceRequest
        import datetime
        sr = db.query(ServiceRequest).filter(ServiceRequest.request_id == str(request_id)).first()
        if sr:
            sr.status = status
            sr.updated_at = datetime.datetime.utcnow()
            db.commit(); db.refresh(sr)
        return sr

    @staticmethod
    def get_available_requests(db, provider_id, skip, limit):
        from app.models.service_request import ServiceRequest, ServiceRequestStatus
        return (
            db.query(ServiceRequest)
            .filter(
                ServiceRequest.status == ServiceRequestStatus.PENDING,
                ServiceRequest.requester_id != str(provider_id),
            ).offset(skip).limit(limit).all()
        )

    @staticmethod
    def get_user_requests(db, requester_id, skip, limit):
        from app.models.service_request import ServiceRequest
        return (
            db.query(ServiceRequest)
            .filter(ServiceRequest.requester_id == str(requester_id))
            .order_by(ServiceRequest.created_at.desc())
            .offset(skip).limit(limit).all()
        )

    @staticmethod
    def update_service_request(db, request_id, update_data):
        from app.models.service_request import ServiceRequest
        import datetime
        sr = db.query(ServiceRequest).filter(ServiceRequest.request_id == str(request_id)).first()
        if sr:
            for field in ['title', 'description', 'offered_amount']:
                if hasattr(update_data, field):
                    val = getattr(update_data, field)
                    if val is not None:
                        setattr(sr, field, val)
            sr.updated_at = datetime.datetime.utcnow()
            db.commit(); db.refresh(sr)
        return sr

    @staticmethod
    def update_payment_status(db, request_id, payment_status):
        from app.models.service_request import ServiceRequest
        import datetime
        sr = db.query(ServiceRequest).filter(ServiceRequest.request_id == str(request_id)).first()
        if sr:
            sr.payment_status = payment_status
            sr.updated_at = datetime.datetime.utcnow()
            db.commit(); db.refresh(sr)
        return sr

    @staticmethod
    def delete_service_request(db, request_id, requester_id):
        from app.models.service_request import ServiceRequest
        sr = db.query(ServiceRequest).filter(ServiceRequest.request_id == str(request_id), ServiceRequest.requester_id == str(requester_id)).first()
        if not sr:
            return False
        db.delete(sr); db.commit(); return True


class ServiceAssignmentCRUD:
    @staticmethod
    def create_assignment(db, assignment_data, provider_id):
        from app.models.service_request import ServiceAssignment, AssignmentStatus
        import datetime
        ect = getattr(assignment_data, 'estimated_completion_time', None)
        if isinstance(ect, str):
            try:
                from datetime import datetime as _dt
                ect = _dt.fromisoformat(ect.replace('Z', '+00:00'))
            except Exception:
                ect = None
        sa = ServiceAssignment(
            assignment_id=str(uuid.uuid4()),
            request_id=assignment_data.request_id,
            provider_id=str(provider_id),
            status=AssignmentStatus.ASSIGNED,
            provider_notes=getattr(assignment_data, 'provider_notes', None),
            estimated_completion_time=ect,
            created_at=datetime.datetime.utcnow(),
            completed_at=None,
        )
        db.add(sa); db.commit(); db.refresh(sa); return sa

    @staticmethod
    def get_assignment_by_request(db, request_id):
        from app.models.service_request import ServiceAssignment
        return db.query(ServiceAssignment).filter(ServiceAssignment.request_id == str(request_id)).first()

    @staticmethod
    def get_assignment(db, assignment_id):
        from app.models.service_request import ServiceAssignment
        return db.query(ServiceAssignment).filter(ServiceAssignment.assignment_id == str(assignment_id)).first()

    @staticmethod
    def update_assignment(db, assignment_id, update_data):
        from app.models.service_request import ServiceAssignment, AssignmentStatus
        import datetime
        sa = db.query(ServiceAssignment).filter(ServiceAssignment.assignment_id == str(assignment_id)).first()
        if sa:
            if hasattr(update_data, 'status') and update_data.status:
                sa.status = AssignmentStatus(update_data.status)
            if hasattr(update_data, 'provider_notes'):
                sa.provider_notes = update_data.provider_notes
            if hasattr(update_data, 'completion_notes'):
                sa.completion_notes = update_data.completion_notes
            if hasattr(update_data, 'estimated_completion_time') and update_data.estimated_completion_time:
                ect = update_data.estimated_completion_time
                if isinstance(ect, str):
                    try:
                        ect = datetime.datetime.fromisoformat(ect.replace('Z', '+00:00'))
                    except Exception:
                        ect = None
                sa.estimated_completion_time = ect
            if sa.status == AssignmentStatus.COMPLETED:
                sa.completed_at = datetime.datetime.utcnow()
            db.commit(); db.refresh(sa)
        return sa

    @staticmethod
    def get_provider_assignments(db, provider_id, skip, limit):
        from app.models.service_request import ServiceAssignment
        return (
            db.query(ServiceAssignment)
            .filter(ServiceAssignment.provider_id == str(provider_id))
            .order_by(ServiceAssignment.created_at.desc())
            .offset(skip).limit(limit).all()
        )


class RatingCRUD:
    @staticmethod
    def create_rating(db, rating_data, rater_id):
        from app.models.service_request import Rating
        import datetime
        rating = Rating(
            rating_id=str(uuid.uuid4()),
            assignment_id=rating_data.assignment_id,
            rater_id=str(rater_id),
            ratee_id=rating_data.ratee_id,
            rating_score=rating_data.rating_score,
            review_text=getattr(rating_data, 'review_text', None),
            is_provider_rating=int(rating_data.is_provider_rating),
            created_at=datetime.datetime.utcnow(),
        )
        db.add(rating); db.commit(); db.refresh(rating); return rating

    @staticmethod
    def check_existing_rating(db, assignment_id, rater_id, is_provider_rating):
        from app.models.service_request import Rating
        return (
            db.query(Rating)
            .filter(
                Rating.assignment_id == str(assignment_id),
                Rating.rater_id == str(rater_id),
                Rating.is_provider_rating == int(is_provider_rating),
            ).first()
        )

    @staticmethod
    def get_rating(db, rating_id):
        from app.models.service_request import Rating
        return db.query(Rating).filter(Rating.rating_id == str(rating_id)).first()

    @staticmethod
    def get_user_ratings_received(db, user_id, skip, limit):
        from app.models.service_request import Rating
        return (
            db.query(Rating)
            .filter(Rating.ratee_id == str(user_id))
            .offset(skip).limit(limit).all()
        )

    @staticmethod
    def get_assignment_ratings(db, assignment_id):
        from app.models.service_request import Rating
        return db.query(Rating).filter(Rating.assignment_id == str(assignment_id)).all()

    @staticmethod
    def calculate_average_rating(db, user_id):
        from app.models.service_request import Rating
        avg = (
            db.query(func.avg(Rating.rating_score))
            .filter(Rating.ratee_id == str(user_id))
            .scalar()
        )
        return float(avg) if avg is not None else 0.0


service_request_crud = ServiceRequestCRUD()
service_assignment_crud = ServiceAssignmentCRUD()
rating_crud = RatingCRUD()
