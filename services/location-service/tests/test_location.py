import pytest

from app.services.location_service import LocationService
from app.schemas.address import AddressCreate
from app.schemas.location import LocationValidationRequest, DistanceCalculationRequest


def test_location_service_imports():
    """Test that LocationService can be imported"""
    assert LocationService is not None


def test_haversine_distance():
    """Test Haversine distance calculation"""
    # Test distance between two known points
    lat1, lon1 = 40.7128, -74.0060  # New York
    lat2, lon2 = 34.0522, -118.2437  # Los Angeles

    distance = LocationService.haversine_distance(lat1, lon1, lat2, lon2)

    # Distance should be approximately 2440 miles
    assert 2400 < distance < 2500


def test_distance_unit_conversion():
    """Test distance unit conversion"""
    distance_miles = 100.0

    # Test miles to kilometers
    km = LocationService.convert_distance(distance_miles, "kilometers")
    assert abs(km - 160.934) < 1.0

    # Test miles to meters
    meters = LocationService.convert_distance(distance_miles, "meters")
    assert abs(meters - 160934.0) < 100.0


def test_location_validation():
    """Test location validation"""
    # Test valid location
    result = LocationService.validate_location(40.7128, -74.0060)
    assert isinstance(result, dict)
    assert "is_valid" in result


def test_address_schema():
    """Test AddressCreate schema validation"""
    address_data = {
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "street_address": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "USA",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "is_primary": False,
        "address_type": "residential",
    }

    address = AddressCreate(**address_data)
    assert address.street_address == "123 Main St"
    assert address.latitude == 40.7128


def test_location_validation_request():
    """Test LocationValidationRequest schema"""
    request_data = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "address": "123 Main St, New York, NY",
    }

    request = LocationValidationRequest(**request_data)
    assert request.latitude == 40.7128
    assert request.longitude == -74.0060


def test_distance_calculation_request():
    """Test DistanceCalculationRequest schema"""
    request_data = {
        "lat1": 40.7128,
        "lon1": -74.0060,
        "lat2": 34.0522,
        "lon2": -118.2437,
        "unit": "miles",
    }

    request = DistanceCalculationRequest(**request_data)
    assert request.lat1 == 40.7128
    assert request.unit == "miles"
