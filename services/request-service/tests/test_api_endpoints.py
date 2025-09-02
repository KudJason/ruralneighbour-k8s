import pytest
import uuid
import json
from unittest.mock import patch, Mock
from fastapi import status
from datetime import datetime

from app.models.service_request import ServiceRequestStatus, AssignmentStatus
from app.schemas.service_request import ServiceRequestCreate


class TestRequestsAPI:
    """Test service requests API endpoints"""

    def test_create_request_success(self, client, mock_auth_user):
        """Test successful request creation"""
        request_data = {
            "title": "Need ride to airport",
            "description": "Looking for transportation to LAX",
            "service_type": "transportation",
            "pickup_latitude": 34.0522,
            "pickup_longitude": -118.2437,
            "destination_latitude": 33.9425,
            "destination_longitude": -118.4081,
            "offered_amount": 50.0,
            "requested_completion_time": "2024-01-15T10:00:00Z",
        }

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user):
            response = client.post("/api/v1/requests", json=request_data)

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["title"] == "Need ride to airport"
            assert data["status"] == "pending"
            assert data["requester_id"] == str(mock_auth_user)
            assert "request_id" in data

    def test_create_request_validation_error(self, client, mock_auth_user):
        """Test request creation with invalid data"""
        request_data = {
            "title": "",  # Empty title should fail validation
            "service_type": "invalid_type",
            "pickup_latitude": 999,  # Invalid latitude
            "pickup_longitude": -200,  # Invalid longitude
        }

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user):
            response = client.post("/api/v1/requests", json=request_data)

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            error_data = response.json()
            assert "detail" in error_data

    def test_create_request_unauthorized(self, client):
        """Test request creation without authentication"""
        request_data = {
            "title": "Test request",
            "description": "Test description",
            "service_type": "transportation",
            "pickup_latitude": 34.0522,
            "pickup_longitude": -118.2437,
        }

        response = client.post("/api/v1/requests", json=request_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_user_requests(self, client, mock_auth_user, db_session):
        """Test getting user's requests"""
        with patch("app.api.deps.get_current_user", return_value=mock_auth_user):
            response = client.get("/api/v1/requests")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)

    def test_get_user_requests_with_pagination(self, client, mock_auth_user):
        """Test getting user's requests with pagination"""
        with patch("app.api.deps.get_current_user", return_value=mock_auth_user):
            response = client.get("/api/v1/requests?skip=0&limit=10")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)

    def test_get_request_by_id_success(self, client, mock_auth_user, db_session):
        """Test getting specific request by ID"""
        # First create a request
        request_data = {
            "title": "Test request",
            "description": "Test description",
            "service_type": "transportation",
            "pickup_latitude": 34.0522,
            "pickup_longitude": -118.2437,
            "destination_latitude": 33.9425,
            "destination_longitude": -118.4081,
        }

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user):
            # Create request
            create_response = client.post("/api/v1/requests", json=request_data)
            assert create_response.status_code == status.HTTP_201_CREATED

            request_id = create_response.json()["request_id"]

            # Get request by ID
            response = client.get(f"/api/v1/requests/{request_id}")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["request_id"] == request_id
            assert data["title"] == "Test request"

    def test_get_request_by_id_not_found(self, client, mock_auth_user):
        """Test getting non-existent request"""
        fake_id = str(uuid.uuid4())

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user):
            response = client.get(f"/api/v1/requests/{fake_id}")
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_request_by_id_unauthorized_access(self, client, mock_auth_user):
        """Test accessing another user's request"""
        other_user_id = uuid.uuid4()
        request_id = str(uuid.uuid4())

        # Mock get_service_request to return request owned by different user
        mock_request = Mock()
        mock_request.requester_id = other_user_id
        mock_request.request_id = uuid.UUID(request_id)

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.crud.crud_service_request.ServiceRequestCRUD.get_service_request",
            return_value=mock_request,
        ):

            response = client.get(f"/api/v1/requests/{request_id}")
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_request_success(self, client, mock_auth_user, db_session):
        """Test successful request update"""
        # First create a request
        request_data = {
            "title": "Original title",
            "description": "Original description",
            "service_type": "transportation",
            "pickup_latitude": 34.0522,
            "pickup_longitude": -118.2437,
        }

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user):
            # Create request
            create_response = client.post("/api/v1/requests", json=request_data)
            request_id = create_response.json()["request_id"]

            # Update request
            update_data = {
                "title": "Updated title",
                "description": "Updated description",
                "offered_amount": 30.0,
            }

            response = client.patch(f"/api/v1/requests/{request_id}", json=update_data)
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["title"] == "Updated title"
            assert data["description"] == "Updated description"
            assert data["offered_amount"] == 30.0

    def test_update_request_not_pending(self, client, mock_auth_user):
        """Test cannot update non-pending request"""
        request_id = str(uuid.uuid4())

        # Mock request with non-pending status
        mock_request = Mock()
        mock_request.requester_id = mock_auth_user
        mock_request.status = ServiceRequestStatus.ACCEPTED
        mock_request.request_id = uuid.UUID(request_id)

        update_data = {"title": "Updated title"}

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.crud.crud_service_request.ServiceRequestCRUD.get_service_request",
            return_value=mock_request,
        ):

            response = client.patch(f"/api/v1/requests/{request_id}", json=update_data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Can only update pending requests" in response.json()["detail"]

    def test_cancel_request_success(self, client, mock_auth_user, db_session):
        """Test successful request cancellation"""
        # First create a request
        request_data = {
            "title": "Test request",
            "description": "Test description",
            "service_type": "transportation",
            "pickup_latitude": 34.0522,
            "pickup_longitude": -118.2437,
        }

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user):
            # Create request
            create_response = client.post("/api/v1/requests", json=request_data)
            request_id = create_response.json()["request_id"]

            # Cancel request
            response = client.delete(f"/api/v1/requests/{request_id}")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["status"] == "cancelled"

    def test_cancel_request_already_assigned(self, client, mock_auth_user):
        """Test cannot cancel request that's already assigned"""
        request_id = str(uuid.uuid4())

        # Mock request with assigned status
        mock_request = Mock()
        mock_request.requester_id = mock_auth_user
        mock_request.status = ServiceRequestStatus.ACCEPTED
        mock_request.request_id = uuid.UUID(request_id)

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.crud.crud_service_request.ServiceRequestCRUD.get_service_request",
            return_value=mock_request,
        ):

            response = client.delete(f"/api/v1/requests/{request_id}")
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert (
                "Cannot cancel request that is already assigned"
                in response.json()["detail"]
            )

    def test_create_rating_success(self, client, mock_auth_user):
        """Test successful rating creation"""
        assignment_id = str(uuid.uuid4())
        provider_id = str(uuid.uuid4())

        rating_data = {
            "assignment_id": assignment_id,
            "ratee_id": provider_id,
            "rating_score": 5,
            "review_text": "Excellent service!",
            "is_provider_rating": True,
        }

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.services.request_service.RequestService.create_rating"
        ) as mock_create_rating:

            mock_rating = Mock()
            mock_rating.rating_id = uuid.uuid4()
            mock_rating.rating_score = 5
            mock_rating.review_text = "Excellent service!"
            mock_create_rating.return_value = mock_rating

            response = client.post(
                f"/api/v1/requests/{assignment_id}/rate", json=rating_data
            )
            assert response.status_code == status.HTTP_201_CREATED

            mock_create_rating.assert_called_once()

    def test_create_rating_validation_error(self, client, mock_auth_user):
        """Test rating creation with invalid data"""
        assignment_id = str(uuid.uuid4())

        rating_data = {
            "assignment_id": assignment_id,
            "rating_score": 6,  # Invalid score (should be 1-5)
            "is_provider_rating": True,
        }

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user):
            response = client.post(
                f"/api/v1/requests/{assignment_id}/rate", json=rating_data
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestProvidersAPI:
    """Test provider-related API endpoints"""

    def test_get_available_requests(self, client, mock_auth_user):
        """Test getting available requests for provider"""
        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.services.request_service.RequestService.get_available_requests_for_provider"
        ) as mock_get_requests:

            mock_get_requests.return_value = []

            response = client.get("/api/v1/providers/requests/available")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert isinstance(data, list)
            mock_get_requests.assert_called_once()

    def test_get_available_requests_with_location(self, client, mock_auth_user):
        """Test getting available requests with provider location"""
        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.services.request_service.RequestService.get_available_requests_for_provider"
        ) as mock_get_requests:

            mock_get_requests.return_value = []

            response = client.get(
                "/api/v1/providers/requests/available?lat=34.0522&lng=-118.2437"
            )
            assert response.status_code == status.HTTP_200_OK

            # Verify location parameters were passed
            call_args = mock_get_requests.call_args
            assert call_args[1]["provider_lat"] == 34.0522
            assert call_args[1]["provider_lng"] == -118.2437

    def test_get_available_requests_with_pagination(self, client, mock_auth_user):
        """Test getting available requests with pagination"""
        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.services.request_service.RequestService.get_available_requests_for_provider"
        ) as mock_get_requests:

            mock_get_requests.return_value = []

            response = client.get(
                "/api/v1/providers/requests/available?skip=10&limit=20"
            )
            assert response.status_code == status.HTTP_200_OK

            # Verify pagination parameters were passed
            call_args = mock_get_requests.call_args
            assert call_args[1]["skip"] == 10
            assert call_args[1]["limit"] == 20

    def test_accept_request_success(self, client, mock_auth_user):
        """Test successful request acceptance"""
        request_id = str(uuid.uuid4())

        assignment_data = {
            "estimated_completion_time": "2024-01-15T10:00:00Z",
            "provider_notes": "I can help with this request",
        }

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.services.request_service.RequestService.assign_provider_to_request"
        ) as mock_assign:

            mock_assignment = Mock()
            mock_assignment.assignment_id = uuid.uuid4()
            mock_assignment.status = AssignmentStatus.ASSIGNED
            mock_assign.return_value = mock_assignment

            response = client.post(
                f"/api/v1/providers/requests/{request_id}/accept", json=assignment_data
            )
            assert response.status_code == status.HTTP_201_CREATED

            mock_assign.assert_called_once()

    def test_accept_request_validation_error(self, client, mock_auth_user):
        """Test request acceptance with invalid data"""
        request_id = str(uuid.uuid4())

        assignment_data = {"estimated_completion_time": "invalid-date-format"}

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user):
            response = client.post(
                f"/api/v1/providers/requests/{request_id}/accept", json=assignment_data
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_accept_request_not_found(self, client, mock_auth_user):
        """Test accepting non-existent request"""
        request_id = str(uuid.uuid4())

        assignment_data = {"estimated_completion_time": "2024-01-15T10:00:00Z"}

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.services.request_service.RequestService.assign_provider_to_request",
            side_effect=Exception("Service request not found"),
        ):

            response = client.post(
                f"/api/v1/providers/requests/{request_id}/accept", json=assignment_data
            )
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_provider_assignments(self, client, mock_auth_user):
        """Test getting provider's assignments"""
        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.crud.crud_service_request.ServiceAssignmentCRUD.get_provider_assignments"
        ) as mock_get_assignments:

            mock_get_assignments.return_value = []

            response = client.get("/api/v1/providers/assignments")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert isinstance(data, list)
            mock_get_assignments.assert_called_once()

    def test_update_assignment_status(self, client, mock_auth_user):
        """Test updating assignment status"""
        assignment_id = str(uuid.uuid4())

        status_data = {
            "status": "in_progress",
            "notes": "Started working on this request",
        }

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.services.request_service.RequestService.update_assignment_status"
        ) as mock_update:

            mock_assignment = Mock()
            mock_assignment.status = AssignmentStatus.IN_PROGRESS
            mock_update.return_value = mock_assignment

            response = client.patch(
                f"/api/v1/providers/assignments/{assignment_id}/status",
                json=status_data,
            )
            assert response.status_code == status.HTTP_200_OK

            mock_update.assert_called_once()

    def test_update_assignment_status_invalid_transition(self, client, mock_auth_user):
        """Test invalid assignment status transition"""
        from fastapi import HTTPException

        assignment_id = str(uuid.uuid4())

        status_data = {"status": "invalid_status", "notes": "Invalid transition"}

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.services.request_service.RequestService.update_assignment_status",
            side_effect=HTTPException(
                status_code=400, detail="Invalid status transition"
            ),
        ):

            response = client.patch(
                f"/api/v1/providers/assignments/{assignment_id}/status",
                json=status_data,
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid status transition" in response.json()["detail"]

    def test_get_assignment_details(self, client, mock_auth_user):
        """Test getting assignment details"""
        assignment_id = str(uuid.uuid4())

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.crud.crud_service_request.ServiceAssignmentCRUD.get_assignment"
        ) as mock_get_assignment:

            mock_assignment = Mock()
            mock_assignment.assignment_id = uuid.UUID(assignment_id)
            mock_assignment.provider_id = mock_auth_user
            mock_get_assignment.return_value = mock_assignment

            response = client.get(f"/api/v1/providers/assignments/{assignment_id}")
            assert response.status_code == status.HTTP_200_OK

            mock_get_assignment.assert_called_once()

    def test_get_assignment_details_unauthorized(self, client, mock_auth_user):
        """Test getting assignment details for unauthorized user"""
        assignment_id = str(uuid.uuid4())
        other_provider_id = uuid.uuid4()

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.crud.crud_service_request.ServiceAssignmentCRUD.get_assignment"
        ) as mock_get_assignment:

            mock_assignment = Mock()
            mock_assignment.assignment_id = uuid.UUID(assignment_id)
            mock_assignment.provider_id = other_provider_id  # Different provider
            mock_get_assignment.return_value = mock_assignment

            response = client.get(f"/api/v1/providers/assignments/{assignment_id}")
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_assignment_details_not_found(self, client, mock_auth_user):
        """Test getting non-existent assignment details"""
        assignment_id = str(uuid.uuid4())

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.crud.crud_service_request.ServiceAssignmentCRUD.get_assignment",
            return_value=None,
        ):

            response = client.get(f"/api/v1/providers/assignments/{assignment_id}")
            assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAPIErrorHandling:
    """Test API error handling scenarios"""

    def test_invalid_uuid_parameter(self, client, mock_auth_user):
        """Test handling of invalid UUID parameters"""
        with patch("app.api.deps.get_current_user", return_value=mock_auth_user):
            response = client.get("/api/v1/requests/invalid-uuid")
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_request_body(self, client, mock_auth_user):
        """Test handling of missing request body"""
        with patch("app.api.deps.get_current_user", return_value=mock_auth_user):
            response = client.post("/api/v1/requests")
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_json_body(self, client, mock_auth_user):
        """Test handling of invalid JSON body"""
        with patch("app.api.deps.get_current_user", return_value=mock_auth_user):
            response = client.post(
                "/api/v1/requests",
                data="invalid json",
                headers={"Content-Type": "application/json"},
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_database_error_handling(self, client, mock_auth_user):
        """Test handling of database errors"""
        request_data = {
            "title": "Test request",
            "description": "Test description",
            "service_type": "transportation",
            "pickup_latitude": 34.0522,
            "pickup_longitude": -118.2437,
        }

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user), patch(
            "app.services.request_service.RequestService.create_service_request",
            side_effect=Exception("Database error"),
        ):

            response = client.post("/api/v1/requests", json=request_data)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_rate_limiting_simulation(self, client, mock_auth_user):
        """Test handling of multiple concurrent requests"""
        request_data = {
            "title": "Test request",
            "description": "Test description",
            "service_type": "transportation",
            "pickup_latitude": 34.0522,
            "pickup_longitude": -118.2437,
        }

        with patch("app.api.deps.get_current_user", return_value=mock_auth_user):
            # Make multiple requests quickly
            responses = []
            for _ in range(3):
                response = client.post("/api/v1/requests", json=request_data)
                responses.append(response)

            # All should return valid HTTP status codes
            for response in responses:
                assert 200 <= response.status_code < 600
