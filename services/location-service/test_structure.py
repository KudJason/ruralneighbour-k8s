#!/usr/bin/env python3
"""
Basic test structure for the Location Service
This file provides a simple way to test the service functionality
"""

import sys
import os
import uuid
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))


def test_imports():
    """Test that all modules can be imported correctly"""
    try:
        from app.models.address import UserAddress
        from app.schemas.address import AddressCreate, AddressResponse
        from app.schemas.location import (
            LocationValidationRequest,
            DistanceCalculationRequest,
        )
        from app.crud.crud_address import address_crud
        from app.services.location_service import LocationService

        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def test_schema_validation():
    """Test Pydantic schema validation"""
    try:
        from app.schemas.address import AddressCreate
        from app.schemas.location import LocationValidationRequest

        # Test address schema
        valid_address_data = {
            "user_id": str(uuid.uuid4()),
            "street_address": "123 Main St",
            "city": "Portland",
            "state": "OR",
            "postal_code": "97201",
            "latitude": 45.5152,
            "longitude": -122.6784,
            "is_primary": True,
        }

        address = AddressCreate(**valid_address_data)
        print("✅ Address schema validation successful")

        # Test location validation schema
        valid_location_data = {
            "latitude": 45.5152,
            "longitude": -122.6784,
            "address": "123 Main St, Portland, OR",
        }

        location = LocationValidationRequest(**valid_location_data)
        print("✅ Location schema validation successful")

        return True
    except Exception as e:
        print(f"❌ Schema validation error: {e}")
        return False


def test_model_creation():
    """Test SQLAlchemy model creation"""
    try:
        from app.models.address import UserAddress

        # Test model creation
        address = UserAddress(
            address_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            street_address="123 Main St",
            city="Portland",
            state="OR",
            postal_code="97201",
            country="USA",
            is_primary=True,
        )

        print("✅ Model creation successful")
        return True
    except Exception as e:
        print(f"❌ Model creation error: {e}")
        return False


def test_location_service():
    """Test location service functionality"""
    try:
        from app.services.location_service import LocationService

        # Test Haversine distance calculation
        distance = LocationService.haversine_distance(
            40.7128, -74.0060, 34.0522, -118.2437
        )
        print(f"✅ Distance calculation successful: {distance:.2f} miles")

        # Test location validation
        validation_result = LocationService.validate_location(45.5152, -122.6784)
        print(f"✅ Location validation successful: {validation_result['is_valid']}")

        # Test distance calculation with different units
        distance_result = LocationService.calculate_distance(
            40.7128, -74.0060, 34.0522, -118.2437, "kilometers"
        )
        print(f"✅ Unit conversion successful: {distance_result['distance']} km")

        return True
    except Exception as e:
        print(f"❌ Location service error: {e}")
        return False


def test_postgis_functions():
    """Test PostGIS-related functions"""
    try:
        from app.services.location_service import LocationService

        # Test point creation
        point = LocationService.create_address_point(45.5152, -122.6784)
        print(f"✅ PostGIS point creation successful: {point}")

        # Test distance conversion
        miles_to_km = LocationService.convert_distance(100.0, "kilometers")
        print(f"✅ Distance conversion successful: {miles_to_km} km")

        return True
    except Exception as e:
        print(f"❌ PostGIS functions error: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Running Location Service tests...")
    print("=" * 50)

    tests = [
        ("Import Test", test_imports),
        ("Schema Validation Test", test_schema_validation),
        ("Model Creation Test", test_model_creation),
        ("Location Service Test", test_location_service),
        ("PostGIS Functions Test", test_postgis_functions),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The service structure is correct.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
