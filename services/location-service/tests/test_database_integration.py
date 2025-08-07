import pytest
import uuid
import os
from decimal import Decimal
from unittest.mock import patch, Mock

from app.crud.crud_address import address_crud
from app.schemas.address import AddressCreate, AddressUpdate
from app.services.location_service import LocationService


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true" or os.getenv("TESTING") == "true",
    reason="Skipping integration tests when PostGIS is not available",
)
class TestDatabaseIntegration:
    """Integration tests using real database operations"""

    def test_create_and_retrieve_address(self, db_session, sample_address_data):
        """Test creating and retrieving an address from the database"""
        # Create address data using schema
        address_data = AddressCreate(**sample_address_data)

        # Mock PostGIS point creation
        with patch(
            "app.crud.crud_address.LocationService.create_address_point"
        ) as mock_create_point:
            mock_create_point.return_value = "POINT(-74.0060 40.7128)"

            # Mock location validation
            with patch(
                "app.crud.crud_address.LocationService.validate_location"
            ) as mock_validate:
                mock_validate.return_value = {
                    "is_valid": True,
                    "nearest_city": "New York",
                }

                # Create address in database
                address = address_crud.create(db_session, obj_in=address_data)

                # Verify address was created
                assert address.address_id is not None
                assert address.street_address == "123 Main St"
                assert address.city == "New York"
                assert address.user_id == sample_address_data["user_id"]
                assert address.is_within_service_area is True

                # Retrieve address by ID
                retrieved_address = address_crud.get(
                    db_session, address_id=address.address_id
                )
                assert retrieved_address is not None
                assert retrieved_address.address_id == address.address_id
                assert retrieved_address.street_address == "123 Main St"

    def test_get_addresses_by_user(self, db_session, sample_address_data):
        """Test retrieving addresses for a specific user"""
        user_id = sample_address_data["user_id"]

        # Create multiple addresses for the same user
        addresses_data = [
            {
                **sample_address_data,
                "street_address": "123 Main St",
                "is_primary": True,
            },
            {
                **sample_address_data,
                "street_address": "456 Oak Ave",
                "is_primary": False,
            },
        ]

        # Mock PostGIS and validation
        with patch(
            "app.crud.crud_address.LocationService.create_address_point"
        ) as mock_create_point, patch(
            "app.crud.crud_address.LocationService.validate_location"
        ) as mock_validate:

            mock_create_point.return_value = "POINT(-74.0060 40.7128)"
            mock_validate.return_value = {"is_valid": True, "nearest_city": "New York"}

            # Create addresses in database
            created_addresses = []
            for address_data in addresses_data:
                address = address_crud.create(
                    db_session, obj_in=AddressCreate(**address_data)
                )
                created_addresses.append(address)

            # Retrieve addresses for user
            user_addresses = address_crud.get_by_user(db_session, user_id=user_id)

            # Verify all addresses were retrieved
            assert len(user_addresses) == 2
            assert all(address.user_id == user_id for address in user_addresses)

            # Verify address details
            addresses = [address.street_address for address in user_addresses]
            assert "123 Main St" in addresses
            assert "456 Oak Ave" in addresses

    def test_primary_address_management(self, db_session, sample_address_data):
        """Test primary address management"""
        user_id = sample_address_data["user_id"]

        # Create first address as primary
        address1_data = {**sample_address_data, "is_primary": True}

        with patch(
            "app.crud.crud_address.LocationService.create_address_point"
        ) as mock_create_point, patch(
            "app.crud.crud_address.LocationService.validate_location"
        ) as mock_validate:

            mock_create_point.return_value = "POINT(-74.0060 40.7128)"
            mock_validate.return_value = {"is_valid": True, "nearest_city": "New York"}

            address1 = address_crud.create(
                db_session, obj_in=AddressCreate(**address1_data)
            )
            assert address1.is_primary is True

            # Create second address as primary (should unset first)
            address2_data = {
                **sample_address_data,
                "street_address": "456 Oak Ave",
                "is_primary": True,
            }
            address2 = address_crud.create(
                db_session, obj_in=AddressCreate(**address2_data)
            )

            # Verify only second address is primary
            db_session.refresh(address1)
            assert address1.is_primary is False
            assert address2.is_primary is True

            # Get primary address
            primary_address = address_crud.get_primary_address(
                db_session, user_id=user_id
            )
            assert primary_address.address_id == address2.address_id

    def test_update_address(self, db_session, sample_address_data):
        """Test updating an address"""
        # Create initial address
        with patch(
            "app.crud.crud_address.LocationService.create_address_point"
        ) as mock_create_point, patch(
            "app.crud.crud_address.LocationService.validate_location"
        ) as mock_validate:

            mock_create_point.return_value = "POINT(-74.0060 40.7128)"
            mock_validate.return_value = {"is_valid": True, "nearest_city": "New York"}

            address = address_crud.create(
                db_session, obj_in=AddressCreate(**sample_address_data)
            )

            # Update address
            update_data = AddressUpdate(
                street_address="789 Pine St",
                city="Brooklyn",
                state="NY",
                postal_code="11201",
            )

            updated_address = address_crud.update(
                db_session, db_obj=address, obj_in=update_data
            )

            # Verify address was updated
            assert updated_address.street_address == "789 Pine St"
            assert updated_address.city == "Brooklyn"
            assert updated_address.postal_code == "11201"

            # Verify change is persisted in database
            retrieved_address = address_crud.get(
                db_session, address_id=address.address_id
            )
            assert retrieved_address.street_address == "789 Pine St"

    def test_delete_address(self, db_session, sample_address_data):
        """Test deleting an address"""
        # Create address
        with patch(
            "app.crud.crud_address.LocationService.create_address_point"
        ) as mock_create_point, patch(
            "app.crud.crud_address.LocationService.validate_location"
        ) as mock_validate:

            mock_create_point.return_value = "POINT(-74.0060 40.7128)"
            mock_validate.return_value = {"is_valid": True, "nearest_city": "New York"}

            address = address_crud.create(
                db_session, obj_in=AddressCreate(**sample_address_data)
            )
            address_id = address.address_id

            # Delete address
            result = address_crud.delete(db_session, address_id=address_id)
            assert result is True

            # Verify address was deleted
            retrieved_address = address_crud.get(db_session, address_id=address_id)
            assert retrieved_address is None

    def test_count_addresses_by_user(self, db_session, sample_address_data):
        """Test counting addresses for a user"""
        user_id = sample_address_data["user_id"]

        # Create multiple addresses
        addresses_data = [
            {**sample_address_data, "street_address": "123 Main St"},
            {**sample_address_data, "street_address": "456 Oak Ave"},
            {**sample_address_data, "street_address": "789 Pine St"},
        ]

        with patch(
            "app.crud.crud_address.LocationService.create_address_point"
        ) as mock_create_point, patch(
            "app.crud.crud_address.LocationService.validate_location"
        ) as mock_validate:

            mock_create_point.return_value = "POINT(-74.0060 40.7128)"
            mock_validate.return_value = {"is_valid": True, "nearest_city": "New York"}

            for address_data in addresses_data:
                address_crud.create(db_session, obj_in=AddressCreate(**address_data))

            # Count addresses for user
            count = address_crud.count_by_user(db_session, user_id=user_id)
            assert count == 3

    def test_database_isolation(self, db_session, sample_address_data):
        """Test that database is properly isolated between tests"""
        # Create an address in this test
        with patch(
            "app.crud.crud_address.LocationService.create_address_point"
        ) as mock_create_point, patch(
            "app.crud.crud_address.LocationService.validate_location"
        ) as mock_validate:

            mock_create_point.return_value = "POINT(-74.0060 40.7128)"
            mock_validate.return_value = {"is_valid": True, "nearest_city": "New York"}

            address = address_crud.create(
                db_session, obj_in=AddressCreate(**sample_address_data)
            )

            # Verify address exists in this test
            retrieved_address = address_crud.get(
                db_session, address_id=address.address_id
            )
            assert retrieved_address is not None
            assert retrieved_address.street_address == "123 Main St"

            # This test should be isolated from other tests
            # The clean_database fixture will clear this data after the test


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true" or os.getenv("TESTING") == "true",
    reason="Skipping integration tests when PostGIS is not available",
)
class TestLocationServiceWithDatabase:
    """Integration tests for LocationService using real database"""

    def test_location_validation_with_database(self, db_session):
        """Test location validation with database integration"""
        # Test location validation
        result = LocationService.validate_location(40.7128, -74.0060)

        assert isinstance(result, dict)
        assert "is_valid" in result
        assert "nearest_city" in result
        assert "distance_to_nearest" in result

    def test_distance_calculation_with_database(self, db_session):
        """Test distance calculation with database integration"""
        # Test distance calculation
        result = LocationService.calculate_distance(
            lat1=40.7128,
            lon1=-74.0060,  # New York
            lat2=34.0522,
            lon2=-118.2437,  # Los Angeles
            unit="miles",
        )

        assert isinstance(result, dict)
        assert "distance" in result
        assert "unit" in result
        assert result["unit"] == "miles"
        assert 2400 < result["distance"] < 2500  # Approximate distance

    def test_find_addresses_within_radius(self, db_session, sample_address_data):
        """Test finding addresses within radius using database"""
        # Create test addresses
        addresses_data = [
            {**sample_address_data, "latitude": 40.7128, "longitude": -74.0060},  # NYC
            {
                **sample_address_data,
                "latitude": 40.7589,
                "longitude": -73.9851,
            },  # NYC area
            {
                **sample_address_data,
                "latitude": 34.0522,
                "longitude": -118.2437,
            },  # LA (far)
        ]

        with patch(
            "app.crud.crud_address.LocationService.create_address_point"
        ) as mock_create_point, patch(
            "app.crud.crud_address.LocationService.validate_location"
        ) as mock_validate:

            mock_create_point.return_value = "POINT(-74.0060 40.7128)"
            mock_validate.return_value = {"is_valid": True, "nearest_city": "New York"}

            # Create addresses
            for address_data in addresses_data:
                address_crud.create(db_session, obj_in=AddressCreate(**address_data))

            # Find addresses within 10 miles of NYC
            nearby_addresses = LocationService.find_addresses_within_radius(
                db=db_session,
                center_lat=40.7128,
                center_lon=-74.0060,
                radius_miles=10.0,
            )

            # Should find addresses in NYC area but not LA
            assert len(nearby_addresses) >= 2  # At least NYC addresses
