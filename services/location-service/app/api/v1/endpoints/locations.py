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
from app.crud.crud_saved_location import saved_location_crud
from app.schemas.saved_location import (
    SavedLocationCreate,
    SavedLocationResponse,
    SavedLocationListResponse,
)

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
    # Standard naming (optional to allow alias-only requests)
    lat1: float = Query(
        None, ge=-90, le=90, description="Latitude of first point"
    ),
    lon1: float = Query(
        None, ge=-180, le=180, description="Longitude of first point"
    ),
    lat2: float = Query(
        None, ge=-90, le=90, description="Latitude of second point"
    ),
    lon2: float = Query(
        None, ge=-180, le=180, description="Longitude of second point"
    ),
    # Alternate naming (optional)
    from_lat: float = Query(
        None, ge=-90, le=90, description="Alias: from latitude"
    ),
    from_lng: float = Query(
        None, ge=-180, le=180, description="Alias: from longitude"
    ),
    to_lat: float = Query(
        None, ge=-90, le=90, description="Alias: to latitude"
    ),
    to_lng: float = Query(
        None, ge=-180, le=180, description="Alias: to longitude"
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

        # Prefer from*/to* if provided
        _lat1 = from_lat if from_lat is not None else lat1
        _lon1 = from_lng if from_lng is not None else lon1
        _lat2 = to_lat if to_lat is not None else lat2
        _lon2 = to_lng if to_lng is not None else lon2

        # Ensure we have all coordinates
        if None in (_lat1, _lon1, _lat2, _lon2):
            raise HTTPException(
                status_code=422,
                detail="Missing required coordinates. Provide either lat1/lon1/lat2/lon2 or from_lat/from_lng/to_lat/to_lng.",
            )

        distance_result = LocationService.calculate_distance(
            _lat1, _lon1, _lat2, _lon2, unit
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


@router.get("/locations/saved", response_model=SavedLocationListResponse)
def get_saved_locations(
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    items = saved_location_crud.list_by_user(db=db, user_id=current_user_id)
    return {"locations": items, "total": len(items)}


@router.post("/locations/saved", response_model=SavedLocationResponse)
def save_location(
    payload: SavedLocationCreate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    item = saved_location_crud.create(
        db=db,
        user_id=current_user_id,
        address=payload.address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        name=payload.name or payload.address,
    )
    # Coerce lat/lon back to float in response
    return SavedLocationResponse(
        location_id=item.location_id,
        user_id=item.user_id,
        name=item.name,
        address=item.address,
        latitude=float(payload.latitude),
        longitude=float(payload.longitude),
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.delete("/locations/saved/{location_id}")
def delete_saved_location(
    location_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    ok = saved_location_crud.delete(db=db, user_id=current_user_id, location_id=location_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Saved location not found")
    return {"message": "Deleted"}
