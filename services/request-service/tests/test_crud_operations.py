import pytest
import os
import uuid
from decimal import Decimal
from datetime import datetime, timedelta

from app.crud.crud_service_request import (
    ServiceRequestCRUD,
    ServiceAssignmentCRUD,
    RatingCRUD,
)
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
    ServiceRequestUpdate,
    ServiceAssignmentCreate,
    ServiceAssignmentUpdate,
    RatingCreate,
)


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true" or os.getenv("TESTING") == "true",
    reason="Skipping integration tests when database is not available",
)
class TestServiceRequestCRUD:
    """Test CRUD operations for service requests"""

    def test_create_service_request(self, db_session):
        """Test creating a service request"""
        requester_id = uuid.uuid4()
        request_data = ServiceRequestCreate(
            title="Need ride to airport",
            description="Looking for transportation to LAX",
            service_type=ServiceType.TRANSPORTATION,
            pickup_latitude=34.0522,
            pickup_longitude=-118.2437,
            destination_latitude=33.9425,
            destination_longitude=-118.4081,
            offered_amount=Decimal("50.00"),
            requested_completion_time="2024-01-15T10:00:00Z",
        )

        service_request = ServiceRequestCRUD.create_service_request(
            db_session, request_data, requester_id
        )

        assert service_request.request_id is not None
        assert service_request.requester_id == str(requester_id)
        assert service_request.title == "Need ride to airport"
        assert service_request.service_type == ServiceType.TRANSPORTATION
        assert service_request.status == ServiceRequestStatus.PENDING
        assert service_request.offered_amount == Decimal("50.00")
        assert service_request.pickup_latitude == 34.0522
        assert service_request.pickup_longitude == -118.2437

    def test_create_service_request_without_amount(self, db_session):
        """Test creating a service request without offered amount"""
        requester_id = uuid.uuid4()
        request_data = ServiceRequestCreate(
            title="Free help request",
            description="Looking for volunteer help",
            service_type=ServiceType.OTHER,
            pickup_latitude=34.0522,
            pickup_longitude=-118.2437,
            destination_latitude=33.9425,
            destination_longitude=-118.4081,
        )

        service_request = ServiceRequestCRUD.create_service_request(
            db_session, request_data, requester_id
        )

        assert service_request.request_id is not None
        assert service_request.offered_amount is None

    def test_get_service_request(self, db_session):
        """Test getting a service request by ID"""
        # Create a request first
        requester_id = uuid.uuid4()
        request_data = ServiceRequestCreate(
            title="Test request",
            description="Test description",
            service_type=ServiceType.ERRANDS,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
        )

        created_request = ServiceRequestCRUD.create_service_request(
            db_session, request_data, requester_id
        )

        # Get the request
        retrieved_request = ServiceRequestCRUD.get_service_request(
            db_session, created_request.request_id
        )

        assert retrieved_request is not None
        assert retrieved_request.request_id == created_request.request_id
        assert retrieved_request.title == "Test request"

    def test_get_service_request_not_found(self, db_session):
        """Test getting non-existent service request"""
        fake_id = uuid.uuid4()
        result = ServiceRequestCRUD.get_service_request(db_session, fake_id)
        assert result is None

    def test_get_user_requests(self, db_session):
        """Test getting requests for a specific user"""
        requester_id = uuid.uuid4()
        other_user_id = uuid.uuid4()

        # Create requests for the user
        for i in range(3):
            request_data = ServiceRequestCreate(
                title=f"Request {i}",
                description=f"Description {i}",
                service_type=ServiceType.TRANSPORTATION,
                pickup_latitude=40.7128,
                pickup_longitude=-74.0060,
            )
            ServiceRequestCRUD.create_service_request(
                db_session, request_data, requester_id
            )

        # Create request for different user
        other_request_data = ServiceRequestCreate(
            title="Other user request",
            description="Other description",
            service_type=ServiceType.TRANSPORTATION,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
        )
        ServiceRequestCRUD.create_service_request(
            db_session, other_request_data, other_user_id
        )

        # Get requests for the user
        user_requests = ServiceRequestCRUD.get_user_requests(
            db_session, requester_id, skip=0, limit=10
        )

        assert len(user_requests) == 3
        for request in user_requests:
            assert request.requester_id == str(requester_id)

    def test_get_user_requests_pagination(self, db_session):
        """Test pagination for user requests"""
        requester_id = uuid.uuid4()

        # Create 5 requests
        for i in range(5):
            request_data = ServiceRequestCreate(
                title=f"Request {i}",
                description=f"Description {i}",
                service_type=ServiceType.TRANSPORTATION,
                pickup_latitude=40.7128,
                pickup_longitude=-74.0060,
            )
            ServiceRequestCRUD.create_service_request(
                db_session, request_data, requester_id
            )

        # Test pagination
        first_page = ServiceRequestCRUD.get_user_requests(
            db_session, requester_id, skip=0, limit=2
        )
        second_page = ServiceRequestCRUD.get_user_requests(
            db_session, requester_id, skip=2, limit=2
        )

        assert len(first_page) == 2
        assert len(second_page) == 2

        # Ensure different requests on each page
        first_page_ids = {req.request_id for req in first_page}
        second_page_ids = {req.request_id for req in second_page}
        assert first_page_ids.isdisjoint(second_page_ids)

    def test_update_service_request(self, db_session):
        """Test updating a service request"""
        requester_id = uuid.uuid4()
        request_data = ServiceRequestCreate(
            title="Original title",
            description="Original description",
            service_type=ServiceType.TRANSPORTATION,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            offered_amount=Decimal("25.00"),
        )

        service_request = ServiceRequestCRUD.create_service_request(
            db_session, request_data, requester_id
        )

        # Update the request
        update_data = ServiceRequestUpdate(
            title="Updated title",
            description="Updated description",
            offered_amount=Decimal("30.00"),
        )

        updated_request = ServiceRequestCRUD.update_service_request(
            db_session, service_request.request_id, update_data
        )

        assert updated_request.title == "Updated title"
        assert updated_request.description == "Updated description"
        assert updated_request.offered_amount == Decimal("30.00")
        assert updated_request.updated_at > updated_request.created_at

    def test_update_request_status(self, db_session):
        """Test updating request status"""
        requester_id = uuid.uuid4()
        request_data = ServiceRequestCreate(
            title="Test request",
            description="Test description",
            service_type=ServiceType.TRANSPORTATION,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
        )

        service_request = ServiceRequestCRUD.create_service_request(
            db_session, request_data, requester_id
        )
        assert service_request.status == ServiceRequestStatus.PENDING

        # Update status
        updated_request = ServiceRequestCRUD.update_request_status(
            db_session, service_request.request_id, ServiceRequestStatus.ACCEPTED
        )

        assert updated_request.status == ServiceRequestStatus.ACCEPTED

    def test_count_user_active_requests(self, db_session):
        """Test counting user's active requests"""
        requester_id = uuid.uuid4()

        # Create various status requests
        statuses = [
            ServiceRequestStatus.PENDING,
            ServiceRequestStatus.ACCEPTED,
            ServiceRequestStatus.IN_PROGRESS,
            ServiceRequestStatus.COMPLETED,
            ServiceRequestStatus.CANCELLED,
        ]

        for status in statuses:
            request_data = ServiceRequestCreate(
                title=f"Request {status.value}",
                description="Test description",
                service_type=ServiceType.TRANSPORTATION,
                pickup_latitude=40.7128,
                pickup_longitude=-74.0060,
            )
            request = ServiceRequestCRUD.create_service_request(
                db_session, request_data, requester_id
            )
            request.status = status
            db_session.commit()

        # Count active requests (PENDING, ACCEPTED, IN_PROGRESS)
        active_count = ServiceRequestCRUD.count_user_active_requests(
            db_session, requester_id
        )
        assert active_count == 3  # PENDING, ACCEPTED, IN_PROGRESS

    def test_get_available_requests(self, db_session):
        """Test getting available requests for providers"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        # Create requests with different statuses
        pending_request_data = ServiceRequestCreate(
            title="Available request",
            description="This should be available",
            service_type=ServiceType.TRANSPORTATION,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
        )
        pending_request = ServiceRequestCRUD.create_service_request(
            db_session, pending_request_data, requester_id
        )

        # Create accepted request (should not be available)
        accepted_request_data = ServiceRequestCreate(
            title="Accepted request",
            description="This should not be available",
            service_type=ServiceType.TRANSPORTATION,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
        )
        accepted_request = ServiceRequestCRUD.create_service_request(
            db_session, accepted_request_data, requester_id
        )
        accepted_request.status = ServiceRequestStatus.ACCEPTED
        db_session.commit()

        # Get available requests
        available_requests = ServiceRequestCRUD.get_available_requests(
            db_session, provider_id, skip=0, limit=10
        )

        # Should only return pending request, not accepted one
        assert len(available_requests) == 1
        assert available_requests[0].request_id == pending_request.request_id
        assert available_requests[0].status == ServiceRequestStatus.PENDING

    def test_get_available_requests_excludes_own_requests(self, db_session):
        """Test that providers don't see their own requests"""
        provider_id = uuid.uuid4()

        # Create request by the provider (acting as requester)
        own_request_data = ServiceRequestCreate(
            title="Own request",
            description="Provider's own request",
            service_type=ServiceType.TRANSPORTATION,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
        )
        ServiceRequestCRUD.create_service_request(
            db_session, own_request_data, provider_id
        )

        # Get available requests for the same user as provider
        available_requests = ServiceRequestCRUD.get_available_requests(
            db_session, provider_id, skip=0, limit=10
        )

        # Should not see own request
        assert len(available_requests) == 0


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true" or os.getenv("TESTING") == "true",
    reason="Skipping integration tests when database is not available",
)
class TestServiceAssignmentCRUD:
    """Test CRUD operations for service assignments"""

    def test_create_assignment(self, db_session):
        """Test creating a service assignment"""
        # First create a service request
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        request_data = ServiceRequestCreate(
            title="Test request",
            description="Test description",
            service_type=ServiceType.TRANSPORTATION,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
        )
        service_request = ServiceRequestCRUD.create_service_request(
            db_session, request_data, requester_id
        )

        # Create assignment
        assignment_data = ServiceAssignmentCreate(
            request_id=service_request.request_id,
            estimated_completion_time="2024-01-15T10:00:00Z",
            provider_notes="I can help with this request",
        )

        assignment = ServiceAssignmentCRUD.create_assignment(
            db_session, assignment_data, provider_id
        )

        assert assignment.assignment_id is not None
        assert assignment.request_id == service_request.request_id
        assert assignment.provider_id == str(provider_id)
        assert assignment.status == AssignmentStatus.ASSIGNED
        assert assignment.provider_notes == "I can help with this request"

    def test_get_assignment(self, db_session):
        """Test getting assignment by ID"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        # Create request and assignment
        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )

        # Get assignment
        retrieved_assignment = ServiceAssignmentCRUD.get_assignment(
            db_session, assignment.assignment_id
        )

        assert retrieved_assignment is not None
        assert retrieved_assignment.assignment_id == assignment.assignment_id
        assert retrieved_assignment.provider_id == str(provider_id)

    def test_get_assignment_by_request(self, db_session):
        """Test getting assignment by request ID"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )

        # Get assignment by request
        retrieved_assignment = ServiceAssignmentCRUD.get_assignment_by_request(
            db_session, service_request.request_id
        )

        assert retrieved_assignment is not None
        assert retrieved_assignment.assignment_id == assignment.assignment_id
        assert retrieved_assignment.request_id == service_request.request_id

    def test_get_provider_assignments(self, db_session):
        """Test getting all assignments for a provider"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()
        other_provider_id = uuid.uuid4()

        # Create multiple assignments for the provider
        for i in range(3):
            service_request = self._create_test_request(
                db_session, requester_id, f"Request {i}"
            )
            self._create_test_assignment(
                db_session, service_request.request_id, provider_id
            )

        # Create assignment for different provider
        other_request = self._create_test_request(
            db_session, requester_id, "Other request"
        )
        self._create_test_assignment(
            db_session, other_request.request_id, other_provider_id
        )

        # Get assignments for the provider
        assignments = ServiceAssignmentCRUD.get_provider_assignments(
            db_session, provider_id, skip=0, limit=10
        )

        assert len(assignments) == 3
        for assignment in assignments:
            assert assignment.provider_id == str(provider_id)

    def test_update_assignment(self, db_session):
        """Test updating assignment"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )

        # Update assignment
        update_data = ServiceAssignmentUpdate(
            status=AssignmentStatus.ACCEPTED,
            provider_notes="Updated notes",
            estimated_completion_time="2024-01-16T10:00:00Z",
        )

        updated_assignment = ServiceAssignmentCRUD.update_assignment(
            db_session, assignment.assignment_id, update_data
        )

        assert updated_assignment.status == AssignmentStatus.ACCEPTED
        assert updated_assignment.provider_notes == "Updated notes"

    def test_update_assignment_completion(self, db_session):
        """Test updating assignment to completed status"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )

        # Update to completed
        update_data = ServiceAssignmentUpdate(
            status=AssignmentStatus.COMPLETED,
            completion_notes="Service completed successfully",
        )

        updated_assignment = ServiceAssignmentCRUD.update_assignment(
            db_session, assignment.assignment_id, update_data
        )

        assert updated_assignment.status == AssignmentStatus.COMPLETED
        assert updated_assignment.completion_notes == "Service completed successfully"
        assert updated_assignment.completed_at is not None

    def _create_test_request(
        self, db_session, requester_id: uuid.UUID, title: str = "Test Request"
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
        )
        return ServiceRequestCRUD.create_service_request(
            db_session, request_data, requester_id
        )

    def _create_test_assignment(
        self, db_session, request_id: uuid.UUID, provider_id: uuid.UUID
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


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true" or os.getenv("TESTING") == "true",
    reason="Skipping integration tests when database is not available",
)
class TestRatingCRUD:
    """Test CRUD operations for ratings"""

    def test_create_rating(self, db_session):
        """Test creating a rating"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        # Create completed assignment
        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )

        # Create rating
        rating_data = RatingCreate(
            assignment_id=assignment.assignment_id,
            ratee_id=str(provider_id),
            rating_score=5,
            review_text="Excellent service!",
            is_provider_rating=True,
        )

        rating = RatingCRUD.create_rating(db_session, rating_data, requester_id)

        assert rating.rating_id is not None
        assert rating.assignment_id == assignment.assignment_id
        assert rating.rater_id == str(requester_id)
        assert rating.ratee_id == str(provider_id)
        assert rating.rating_score == 5
        assert rating.review_text == "Excellent service!"
        assert rating.is_provider_rating_bool is True

    def test_get_rating(self, db_session):
        """Test getting rating by ID"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )

        rating_data = RatingCreate(
            assignment_id=assignment.assignment_id,
            ratee_id=str(provider_id),
            rating_score=4,
            is_provider_rating=True,
        )

        rating = RatingCRUD.create_rating(db_session, rating_data, requester_id)

        # Get rating
        retrieved_rating = RatingCRUD.get_rating(db_session, rating.rating_id)

        assert retrieved_rating is not None
        assert retrieved_rating.rating_id == rating.rating_id
        assert retrieved_rating.rating_score == 4

    def test_get_user_ratings_received(self, db_session):
        """Test getting ratings received by a user"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()
        other_user_id = uuid.uuid4()

        # Create ratings for the provider
        for i in range(3):
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
            RatingCRUD.create_rating(db_session, rating_data, requester_id)

        # Create rating for different user
        other_request = self._create_test_request(db_session, other_user_id)
        other_assignment = self._create_test_assignment(
            db_session, other_request.request_id, other_user_id
        )
        other_rating_data = RatingCreate(
            assignment_id=other_assignment.assignment_id,
            ratee_id=str(other_user_id),
            rating_score=3,
            is_provider_rating=True,
        )
        RatingCRUD.create_rating(db_session, other_rating_data, requester_id)

        # Get ratings for the provider
        provider_ratings = RatingCRUD.get_user_ratings_received(
            db_session, provider_id, skip=0, limit=10
        )

        assert len(provider_ratings) == 3
        for rating in provider_ratings:
            assert rating.ratee_id == str(provider_id)

    def test_get_assignment_ratings(self, db_session):
        """Test getting all ratings for an assignment"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )

        # Create provider rating (requester rates provider)
        provider_rating_data = RatingCreate(
            assignment_id=assignment.assignment_id,
            ratee_id=str(provider_id),
            rating_score=5,
            is_provider_rating=True,
        )
        RatingCRUD.create_rating(db_session, provider_rating_data, requester_id)

        # Create requester rating (provider rates requester)
        requester_rating_data = RatingCreate(
            assignment_id=assignment.assignment_id,
            ratee_id=str(requester_id),
            rating_score=4,
            is_provider_rating=False,
        )
        RatingCRUD.create_rating(db_session, requester_rating_data, provider_id)

        # Get all ratings for assignment
        assignment_ratings = RatingCRUD.get_assignment_ratings(
            db_session, assignment.assignment_id
        )

        assert len(assignment_ratings) == 2

        # Check both ratings exist
        provider_ratings = [r for r in assignment_ratings if r.is_provider_rating]
        requester_ratings = [r for r in assignment_ratings if not r.is_provider_rating]

        assert len(provider_ratings) == 1
        assert len(requester_ratings) == 1
        assert provider_ratings[0].rating_score == 5
        assert requester_ratings[0].rating_score == 4

    def test_check_existing_rating(self, db_session):
        """Test checking if rating already exists"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        service_request = self._create_test_request(db_session, requester_id)
        assignment = self._create_test_assignment(
            db_session, service_request.request_id, provider_id
        )

        # No rating exists initially
        existing = RatingCRUD.check_existing_rating(
            db_session, assignment.assignment_id, requester_id, True
        )
        assert existing is None

        # Create rating
        rating_data = RatingCreate(
            assignment_id=assignment.assignment_id,
            ratee_id=str(provider_id),
            rating_score=5,
            is_provider_rating=True,
        )
        RatingCRUD.create_rating(db_session, rating_data, requester_id)

        # Now rating should exist
        existing = RatingCRUD.check_existing_rating(
            db_session, assignment.assignment_id, requester_id, True
        )
        assert existing is not None

    def test_calculate_average_rating(self, db_session):
        """Test calculating average rating for a user"""
        requester_id = uuid.uuid4()
        provider_id = uuid.uuid4()

        # Create multiple ratings for the provider
        scores = [5, 4, 5, 3, 4]
        for score in scores:
            service_request = self._create_test_request(db_session, requester_id)
            assignment = self._create_test_assignment(
                db_session, service_request.request_id, provider_id
            )

            rating_data = RatingCreate(
                assignment_id=assignment.assignment_id,
                ratee_id=str(provider_id),
                rating_score=score,
                is_provider_rating=True,
            )
            RatingCRUD.create_rating(db_session, rating_data, requester_id)

        # Calculate average
        average = RatingCRUD.calculate_average_rating(db_session, provider_id)
        expected_average = sum(scores) / len(scores)

        assert (
            abs(average - expected_average) < 0.01
        )  # Allow small floating point difference

    def test_calculate_average_rating_no_ratings(self, db_session):
        """Test calculating average rating when no ratings exist"""
        user_id = uuid.uuid4()
        average = RatingCRUD.calculate_average_rating(db_session, user_id)
        assert average == 0.0

    def _create_test_request(
        self, db_session, requester_id: uuid.UUID
    ) -> ServiceRequest:
        """Helper method to create test service request"""
        request_data = ServiceRequestCreate(
            title="Test Request",
            description="Test description",
            service_type=ServiceType.TRANSPORTATION,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            destination_latitude=40.7589,
            destination_longitude=-73.9851,
        )
        return ServiceRequestCRUD.create_service_request(
            db_session, request_data, requester_id
        )

    def _create_test_assignment(
        self, db_session, request_id: uuid.UUID, provider_id: uuid.UUID
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
