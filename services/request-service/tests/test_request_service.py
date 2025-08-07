import pytest
import uuid
from decimal import Decimal
from unittest.mock import patch, Mock
from sqlalchemy.orm import Session

from app.services.request_service import RequestService
from app.models.service_request import (
    ServiceRequest,
    ServiceAssignment,
    Rating,
    ServiceRequestStatus,
    AssignmentStatus,
    ServiceType,
)
from app.schemas.service_request import (
    ServiceRequestCreate,
    ServiceAssignmentCreate,
    RatingCreate,
    StatusUpdateRequest,
)
from app.crud.crud_service_request import (
    ServiceRequestCRUD,
    ServiceAssignmentCRUD,
    RatingCRUD,
)
from fastapi import HTTPException


class TestRequestService:
    """Test RequestService business logic"""

    def test_create_service_request_success(self, db_session, mock_redis):
        """Test successful service request creation"""
        requester_id = uuid.uuid4()
        request_data = ServiceRequestCreate(
            title="Need ride to airport",
            description="Need transportation to LAX airport",
            service_type=ServiceType.TRANSPORTATION,
            pickup_latitude=34.0522,
            pickup_longitude=-118.2437,
            destination_latitude=33.9425,
            destination_longitude=-118.4081,
            offered_amount=Decimal("50.00"),
        )

        # Mock event publishing to avoid Redis dependency
        with patch(
            "app.services.request_service.EventPublisher.publish_service_request_created"
        ) as mock_publish:
            service_request = RequestService.create_service_request(
                db_session, request_data, requester_id
            )

            # Verify request was created
            assert service_request.request_id is not None
            assert service_request.requester_id == str(requester_id)
            assert service_request.title == "Need ride to airport"
            assert service_request.status == ServiceRequestStatus.PENDING
            assert service_request.offered_amount == Decimal("50.00")

            # Verify event was published
            mock_publish.assert_called_once()
            call_args = mock_publish.call_args[1]
            assert call_args["request_id"] == str(service_request.request_id)
            assert call_args["requester_id"] == str(requester_id)
            assert call_args["service_type"] == "transportation"
            assert call_args["offered_amount"] == 50.0

    def test_create_service_request_max_limit_reached(self, db_session):
        """Test creating request when user has reached maximum limit"""
        requester_id = uuid.uuid4()

        # Mock count to return max limit
        with patch.object(
            ServiceRequestCRUD, "count_user_active_requests", return_value=5
        ):
            request_data = ServiceRequestCreate(
                title="Test request",
                description="Test description",
                service_type=ServiceType.TRANSPORTATION,
                pickup_latitude=34.0522,
                pickup_longitude=-118.2437,
                destination_latitude=33.9425,
                destination_longitude=-118.4081,
            )

            with pytest.raises(HTTPException) as exc_info:
                RequestService.create_service_request(
                    db_session, request_data, requester_id
                )

            assert exc_info.value.status_code == 400
            assert "Maximum 5 active requests allowed" in str(exc_info.value.detail)

    def test_create_service_request_event_publishing_failure(self, db_session):
        """Test request creation continues even if event publishing fails"""
        requester_id = uuid.uuid4()
        request_data = ServiceRequestCreate(
            title="Test request",
            description="Test description",
            service_type=ServiceType.ERRANDS,
            pickup_latitude=34.0522,
            pickup_longitude=-118.2437,
            destination_latitude=33.9425,
            destination_longitude=-118.4081,
        )

        # Mock event publishing to raise exception
        with patch(
            "app.services.request_service.EventPublisher.publish_service_request_created",
            side_effect=Exception("Redis error"),
        ):
            # Should not raise exception, just log error
            service_request = RequestService.create_service_request(
                db_session, request_data, requester_id
            )

            # Request should still be created
            assert service_request.request_id is not None
            assert service_request.status == ServiceRequestStatus.PENDING

    def test_assign_provider_to_request_success(self, db_session):
        """Test successful provider assignment"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        # Create a service request first
        service_request = self._create_test_request(db_session, requester_id)

        assignment_data = ServiceAssignmentCreate(
            request_id=service_request.request_id,
            estimated_completion_time="2024-01-15T10:00:00Z",
            provider_notes="I can help with this request",
        )

        with patch(
            "app.services.request_service.EventPublisher.publish_request_status_changed"
        ) as mock_publish:
            assignment = RequestService.assign_provider_to_request(
                db_session, service_request.request_id, provider_id, assignment_data
            )

            # Verify assignment was created
            assert assignment.assignment_id is not None
            assert assignment.provider_id == str(provider_id)
            assert assignment.request_id == service_request.request_id
            assert assignment.status == AssignmentStatus.ASSIGNED

            # Verify request status was updated
            db_session.refresh(service_request)
            assert service_request.status == ServiceRequestStatus.ACCEPTED

            # Verify event was published
            mock_publish.assert_called_once()

    def test_assign_provider_to_request_not_found(self, db_session):
        """Test assignment to non-existent request"""
        provider_id = uuid.uuid4()
        fake_request_id = uuid.uuid4()

        assignment_data = ServiceAssignmentCreate(
            request_id=str(fake_request_id),
            estimated_completion_time="2024-01-15T10:00:00Z",
        )

        with pytest.raises(HTTPException) as exc_info:
            RequestService.assign_provider_to_request(
                db_session, fake_request_id, provider_id, assignment_data
            )

        assert exc_info.value.status_code == 404
        assert "Service request not found" in str(exc_info.value.detail)

    def test_assign_provider_to_request_not_available(self, db_session):
        """Test assignment to request that's no longer available"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        # Create request and mark as completed
        service_request = self._create_test_request(db_session, requester_id)
        service_request.status = ServiceRequestStatus.COMPLETED
        db_session.commit()

        assignment_data = ServiceAssignmentCreate(
            request_id=service_request.request_id,
            estimated_completion_time="2024-01-15T10:00:00Z",
        )

        with pytest.raises(HTTPException) as exc_info:
            RequestService.assign_provider_to_request(
                db_session, service_request.request_id, provider_id, assignment_data
            )

        assert exc_info.value.status_code == 400
        assert "no longer available" in str(exc_info.value.detail)

    def test_assign_provider_to_own_request(self, db_session):
        """Test provider cannot assign to their own request"""
        requester_id = uuid.uuid4()

        # Create request
        service_request = self._create_test_request(db_session, requester_id)

        assignment_data = ServiceAssignmentCreate(
            request_id=service_request.request_id,
            estimated_completion_time="2024-01-15T10:00:00Z",
        )

        # Try to assign requester as provider
        with pytest.raises(HTTPException) as exc_info:
            RequestService.assign_provider_to_request(
                db_session, service_request.request_id, requester_id, assignment_data
            )

        assert exc_info.value.status_code == 400
        assert "Cannot assign to your own request" in str(exc_info.value.detail)

    def test_update_assignment_status_success(self, db_session):
        """Test successful assignment status update"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        # Create request and assignment
        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )

        status_data = StatusUpdateRequest(
            status="accepted", notes="I accept this assignment"
        )

        with patch(
            "app.services.request_service.EventPublisher.publish_request_status_changed"
        ) as mock_publish:
            updated_assignment = RequestService.update_assignment_status(
                db_session, assignment.assignment_id, status_data, provider_id
            )

            # Verify status was updated
            assert updated_assignment.status == AssignmentStatus.ACCEPTED
            assert updated_assignment.provider_notes == "I accept this assignment"

            # Verify event was published
            mock_publish.assert_called_once()

    def test_update_assignment_status_invalid_transition(self, db_session):
        """Test invalid status transition"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        # Create completed assignment
        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )
        assignment.status = AssignmentStatus.COMPLETED
        db_session.commit()

        status_data = StatusUpdateRequest(
            status="in_progress", notes="Trying to change completed status"
        )

        with pytest.raises(HTTPException) as exc_info:
            RequestService.update_assignment_status(
                db_session, assignment.assignment_id, status_data, provider_id
            )

        assert exc_info.value.status_code == 400
        assert "Invalid status transition" in str(exc_info.value.detail)

    def test_update_assignment_status_unauthorized(self, db_session):
        """Test unauthorized user cannot update assignment"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()
        unauthorized_user_id = uuid.uuid4()

        # Create request and assignment
        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )

        status_data = StatusUpdateRequest(
            status="accepted", notes="Unauthorized update"
        )

        with pytest.raises(HTTPException) as exc_info:
            RequestService.update_assignment_status(
                db_session, assignment.assignment_id, status_data, unauthorized_user_id
            )

        assert exc_info.value.status_code == 403
        assert "Not authorized" in str(exc_info.value.detail)

    def test_create_rating_success(self, db_session):
        """Test successful rating creation"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        # Create completed assignment
        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )
        assignment.status = AssignmentStatus.COMPLETED
        db_session.commit()

        rating_data = RatingCreate(
            assignment_id=assignment.assignment_id,
            ratee_id=str(provider_id),
            rating_score=5,
            review_text="Excellent service!",
            is_provider_rating=True,
        )

        with patch(
            "app.services.request_service.EventPublisher.publish_rating_created"
        ) as mock_publish:
            rating = RequestService.create_rating(db_session, rating_data, requester_id)

            # Verify rating was created
            assert rating.rating_id is not None
            assert rating.rater_id == str(requester_id)
            assert rating.ratee_id == str(provider_id)
            assert rating.rating_score == 5
            assert rating.is_provider_rating_bool is True

            # Verify event was published
            mock_publish.assert_called_once()

    def test_create_rating_not_completed(self, db_session):
        """Test cannot rate incomplete service"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        # Create assignment that's not completed
        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )

        rating_data = RatingCreate(
            assignment_id=assignment.assignment_id,
            ratee_id=str(provider_id),
            rating_score=5,
            is_provider_rating=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            RequestService.create_rating(db_session, rating_data, requester_id)

        assert exc_info.value.status_code == 400
        assert "Can only rate completed services" in str(exc_info.value.detail)

    def test_create_rating_unauthorized_rater(self, db_session):
        """Test unauthorized user cannot create rating"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()
        unauthorized_user_id = uuid.uuid4()

        # Create completed assignment
        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )
        assignment.status = AssignmentStatus.COMPLETED
        db_session.commit()

        rating_data = RatingCreate(
            assignment_id=assignment.assignment_id,
            ratee_id=str(provider_id),
            rating_score=5,
            is_provider_rating=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            RequestService.create_rating(db_session, rating_data, unauthorized_user_id)

        assert exc_info.value.status_code == 403
        assert "Only the requester can rate the provider" in str(exc_info.value.detail)

    def test_get_available_requests_for_provider(self, db_session):
        """Test getting available requests for provider"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        # Create multiple requests
        request1 = self._create_test_request(db_session, requester_id, "Request 1")
        request2 = self._create_test_request(db_session, requester_id, "Request 2")

        # Mock CRUD method
        with patch.object(
            ServiceRequestCRUD,
            "get_available_requests",
            return_value=[request1, request2],
        ):
            requests = RequestService.get_available_requests_for_provider(
                db_session, provider_id, skip=0, limit=10
            )

            assert len(requests) == 2
            assert requests[0].title == "Request 1"
            assert requests[1].title == "Request 2"

    def test_get_available_requests_with_distance_filter(self, db_session):
        """Test getting available requests with distance filtering"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        # Create requests at different distances
        close_request = self._create_test_request(
            db_session, requester_id, "Close Request"
        )
        close_request.pickup_latitude = Decimal("40.7128")  # NYC
        close_request.pickup_longitude = Decimal("-74.0060")

        far_request = self._create_test_request(db_session, requester_id, "Far Request")
        far_request.pickup_latitude = Decimal("34.0522")  # LA
        far_request.pickup_longitude = Decimal("-118.2437")

        db_session.commit()

        # Mock CRUD method
        with patch.object(
            ServiceRequestCRUD,
            "get_available_requests",
            return_value=[close_request, far_request],
        ):
            # Provider in NYC
            requests = RequestService.get_available_requests_for_provider(
                db_session,
                provider_id,
                provider_lat=40.7128,
                provider_lng=-74.0060,
                skip=0,
                limit=10,
            )

            # Should only return close request (within 2 mile radius)
            assert len(requests) == 1
            assert requests[0].title == "Close Request"
            assert hasattr(requests[0], "distance_miles")

    def test_calculate_distance(self):
        """Test distance calculation using Haversine formula"""
        # Test distance between NYC and LA (approximately 2445 miles)
        distance = RequestService._calculate_distance(
            40.7128, -74.0060, 34.0522, -118.2437  # NYC  # LA
        )

        # Should be approximately 2445 miles (within 100 mile tolerance)
        assert 2300 <= distance <= 2600

        # Test distance between close points (should be small)
        distance = RequestService._calculate_distance(
            40.7128, -74.0060, 40.7589, -73.9851  # NYC  # Central Park (about 5 miles)
        )

        assert distance < 10  # Should be less than 10 miles

    def _create_test_request(
        self, db_session: Session, requester_id: uuid.UUID, title: str = "Test Request"
    ) -> ServiceRequest:
        """Helper method to create test service request"""
        request_data = ServiceRequestCreate(
            title=title,
            description="Test description",
            service_type=ServiceType.TRANSPORTATION,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            destination_latitude=40.7589,
            destination_longitude=-73.9851,
            offered_amount=Decimal("25.00"),
        )

        return ServiceRequestCRUD.create_service_request(
            db_session, request_data, requester_id
        )

    def _create_test_assignment(
        self, db_session: Session, request_id: uuid.UUID, provider_id: uuid.UUID
    ) -> ServiceAssignment:
        """Helper method to create test assignment"""
        assignment_data = ServiceAssignmentCreate(
            request_id=request_id,
            estimated_completion_time="2024-01-15T10:00:00Z",
            provider_notes="Test assignment",
        )

        return ServiceAssignmentCRUD.create_assignment(
            db_session, assignment_data, provider_id
        )


class TestRequestServiceEdgeCases:
    """Test edge cases and error conditions"""

    def test_create_service_request_with_none_amount(self, db_session):
        """Test creating request without offered amount"""
        requester_id = uuid.uuid4()
        request_data = ServiceRequestCreate(
            title="Free help request",
            description="Looking for volunteer help",
            service_type=ServiceType.OTHER,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            destination_latitude=40.7589,
            destination_longitude=-73.9851,
            # No offered_amount
        )

        with patch(
            "app.services.request_service.EventPublisher.publish_service_request_created"
        ) as mock_publish:
            service_request = RequestService.create_service_request(
                db_session, request_data, requester_id
            )

            assert service_request.offered_amount is None

            # Verify event published with None amount
            call_args = mock_publish.call_args[1]
            assert call_args["offered_amount"] is None

    def test_update_assignment_status_service_completed_event(self, db_session):
        """Test ServiceCompleted event is published when status changes to completed"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        # Create assignment in progress
        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )
        assignment.status = AssignmentStatus.IN_PROGRESS
        db_session.commit()

        status_data = StatusUpdateRequest(
            status="completed", notes="Service completed successfully"
        )

        with patch(
            "app.services.request_service.EventPublisher.publish_request_status_changed"
        ) as mock_status_publish, patch(
            "app.services.request_service.EventPublisher.publish_service_completed"
        ) as mock_completed_publish:

            RequestService.update_assignment_status(
                db_session, assignment.assignment_id, status_data, provider_id
            )

            # Both events should be published
            mock_status_publish.assert_called_once()
            mock_completed_publish.assert_called_once()

    def test_create_rating_duplicate_rating(self, db_session):
        """Test cannot create duplicate rating"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        # Create completed assignment
        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )
        assignment.status = AssignmentStatus.COMPLETED
        db_session.commit()

        rating_data = RatingCreate(
            assignment_id=assignment.assignment_id,
            ratee_id=str(provider_id),
            rating_score=5,
            is_provider_rating=True,
        )

        # Mock existing rating check to return existing rating
        with patch.object(RatingCRUD, "check_existing_rating", return_value=True):
            with pytest.raises(HTTPException) as exc_info:
                RequestService.create_rating(db_session, rating_data, requester_id)

            assert exc_info.value.status_code == 400
            assert "Rating already exists" in str(exc_info.value.detail)

    def test_assignment_with_existing_assignment(self, db_session):
        """Test cannot assign provider when assignment already exists"""
        requester_id = uuid.uuid4()
        provider_id1 = uuid.uuid4()
        provider_id2 = uuid.uuid4()

        # Create request and first assignment
        service_request = self._create_test_request(db_session, requester_id)
        existing_assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id1
        )

        assignment_data = ServiceAssignmentCreate(
            request_id=service_request.request_id,
            estimated_completion_time="2024-01-15T10:00:00Z",
        )

        # Mock existing assignment check
        with patch.object(
            ServiceAssignmentCRUD,
            "get_assignment_by_request",
            return_value=existing_assignment,
        ):
            with pytest.raises(HTTPException) as exc_info:
                RequestService.assign_provider_to_request(
                    db_session,
                    service_request.request_id,
                    provider_id2,
                    assignment_data,
                )

            assert exc_info.value.status_code == 400
            assert "already has an assignment" in str(exc_info.value.detail)

    def _create_test_request(
        self, db_session: Session, requester_id: uuid.UUID, title: str = "Test Request"
    ) -> ServiceRequest:
        """Helper method to create test service request"""
        request_data = ServiceRequestCreate(
            title=title,
            description="Test description",
            service_type=ServiceType.TRANSPORTATION,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            destination_latitude=40.7589,
            destination_longitude=-73.9851,
            offered_amount=Decimal("25.00"),
        )

        return ServiceRequestCRUD.create_service_request(
            db_session, request_data, requester_id
        )

    def _create_test_assignment(
        self, db_session: Session, request_id: uuid.UUID, provider_id: uuid.UUID
    ) -> ServiceAssignment:
        """Helper method to create test assignment"""
        assignment_data = ServiceAssignmentCreate(
            request_id=request_id,
            estimated_completion_time="2024-01-15T10:00:00Z",
            provider_notes="Test assignment",
        )

        return ServiceAssignmentCRUD.create_assignment(
            db_session, assignment_data, provider_id
        )
