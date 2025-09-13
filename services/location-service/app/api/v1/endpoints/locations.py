import time
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.base import get_db
from app.core.config import settings
from app.crud.crud_address import address_crud
from app.schemas.location import (
    DistanceCalculationRequest,
    DistanceCalculationResponse,
    LocationValidationRequest,
    LocationValidationResponse,
)
from app.services.location_service import LocationService

router = APIRouter()


@router.post("/locations/validate", response_model=LocationValidationResponse)
def validate_location(
    request: LocationValidationRequest,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Validate a location against business rules.

    Rule: Users cannot live within 2 miles of a city with population > 50,000
    """
    start_time = time.time()

    try:
        validation_result = LocationService.validate_location(
            request.latitude, request.longitude
        )

        # Check performance requirement (under 200ms)
        query_time = (time.time() - start_time) * 1000
        if query_time > settings.MAX_QUERY_TIME_MS:
            print(
                f"Warning: Location validation took {query_time:.2f}ms (exceeds {settings.MAX_QUERY_TIME_MS}ms limit)"
            )

        return LocationValidationResponse(
            is_valid=validation_result["is_valid"],
            latitude=request.latitude,
            longitude=request.longitude,
            distance_to_restricted_area=validation_result.get(
                "distance_to_restricted_area"
            ),
            nearest_restricted_city=validation_result.get("nearest_restricted_city"),
            population_of_nearest_city=validation_result.get(
                "population_of_nearest_city"
            ),
            message=validation_result["message"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/locations/distance", response_model=DistanceCalculationResponse)
def calculate_distance(
    lat1: float = Query(
        ..., ge=-90, le=90, description="Latitude of first point"
    ),
    lon1: float = Query(
        ..., ge=-180, le=180, description="Longitude of first point"
    ),
    lat2: float = Query(
        ..., ge=-90, le=90, description="Latitude of second point"
    ),
    lon2: float = Query(
        ..., ge=-180, le=180, description="Longitude of second point"
    ),
    unit: str = Query(
        "miles", description="Distance unit: miles, kilometers, meters"
    ),
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Calculate distance between two points using Haversine formula.

    Supports multiple units: miles, kilometers, meters
    """
    start_time = time.time()

    try:
        # Validate unit parameter
        valid_units = ["miles", "kilometers", "meters"]
        if unit.lower() not in valid_units:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid unit. Must be one of: {', '.join(valid_units)}",
            )

        distance_result = LocationService.calculate_distance(
            lat1, lon1, lat2, lon2, unit
        )

        # Check performance requirement (under 200ms)
        query_time = (time.time() - start_time) * 1000
        if query_time > settings.MAX_QUERY_TIME_MS:
            print(
                f"Warning: Distance calculation took {query_time:.2f}ms (exceeds {settings.MAX_QUERY_TIME_MS}ms limit)"
            )

        return DistanceCalculationResponse(**distance_result)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Distance calculation failed: {str(e)}"
        )


@router.get("/locations/performance")
def check_performance(
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Check performance metrics for geospatial queries.
    This endpoint helps monitor if queries are meeting the 200ms requirement.
    """
    performance_tests = []

    # Test 1: Location validation
    start_time = time.time()
    LocationService.validate_location(40.7128, -74.0060)  # New York
    validation_time = (time.time() - start_time) * 1000
    performance_tests.append(
        {
            "test": "Location Validation",
            "time_ms": round(validation_time, 2),
            "within_limit": validation_time <= settings.MAX_QUERY_TIME_MS,
        }
    )

    # Test 2: Distance calculation
    start_time = time.time()
    LocationService.calculate_distance(
        40.7128, -74.0060, 34.0522, -118.2437
    )  # NY to LA
    distance_time = (time.time() - start_time) * 1000
    performance_tests.append(
        {
            "test": "Distance Calculation",
            "time_ms": round(distance_time, 2),
            "within_limit": distance_time <= settings.MAX_QUERY_TIME_MS,
        }
    )

    # Test 3: Spatial query (if database is available)
    try:
        start_time = time.time()
        address_crud.find_within_radius(db, 40.7128, -74.0060, 10.0)
        spatial_time = (time.time() - start_time) * 1000
        performance_tests.append(
            {
                "test": "Spatial Query",
                "time_ms": round(spatial_time, 2),
                "within_limit": spatial_time <= settings.MAX_QUERY_TIME_MS,
            }
        )
    except Exception as e:
        performance_tests.append(
            {
                "test": "Spatial Query",
                "time_ms": "N/A",
                "within_limit": "Error",
                "error": str(e),
            }
        )

    return {
        "performance_tests": performance_tests,
        "max_allowed_time_ms": settings.MAX_QUERY_TIME_MS,
        "all_tests_passing": all(
            test.get("within_limit") == True
            for test in performance_tests
            if test.get("within_limit") != "Error"
        ),
    }
