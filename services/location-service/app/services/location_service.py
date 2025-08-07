import math
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.models.address import UserAddress
from app.core.config import settings


class LocationService:
    """Service for location validation and distance calculations"""

    # Earth's radius in miles
    EARTH_RADIUS_MILES = 3959.0

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the Haversine distance between two points on Earth.

        Args:
            lat1, lon1: Coordinates of first point
            lat2, lon2: Coordinates of second point

        Returns:
            Distance in miles
        """
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return LocationService.EARTH_RADIUS_MILES * c

    @staticmethod
    def convert_distance(distance_miles: float, unit: str) -> float:
        """Convert distance from miles to other units"""
        if unit.lower() == "kilometers":
            return distance_miles * 1.60934
        elif unit.lower() == "meters":
            return distance_miles * 1609.34
        else:
            return distance_miles  # Default to miles

    @staticmethod
    def validate_location(latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Validate location against business rules.
        Rule: Users cannot live within 2 miles of a city with population > 50,000

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Dictionary with validation results
        """
        # For demo purposes, we'll use a simplified validation
        # In a real implementation, this would query a database of cities with populations

        # Example restricted cities (in real implementation, this would come from a database)
        restricted_cities = [
            {
                "name": "New York",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "population": 8336817,
            },
            {
                "name": "Los Angeles",
                "latitude": 34.0522,
                "longitude": -118.2437,
                "population": 3979576,
            },
            {
                "name": "Chicago",
                "latitude": 41.8781,
                "longitude": -87.6298,
                "population": 2693976,
            },
        ]

        min_distance = float("inf")
        nearest_city = None

        # Check distance to each restricted city
        for city in restricted_cities:
            if city["population"] > settings.RESTRICTED_CITY_POPULATION_THRESHOLD:
                distance = LocationService.haversine_distance(
                    latitude, longitude, city["latitude"], city["longitude"]
                )

                if distance < min_distance:
                    min_distance = distance
                    nearest_city = city

        # Check if location is within restricted area
        is_valid = min_distance > settings.RESTRICTED_AREA_RADIUS_MILES

        return {
            "is_valid": is_valid,
            "distance_to_restricted_area": (
                min_distance if min_distance != float("inf") else None
            ),
            "nearest_restricted_city": nearest_city["name"] if nearest_city else None,
            "population_of_nearest_city": (
                nearest_city["population"] if nearest_city else None
            ),
            "message": (
                f"Location is {'valid' if is_valid else 'invalid'}. "
                f"Distance to nearest restricted city: {min_distance:.2f} miles"
                if min_distance != float("inf")
                else "Location is valid. No restricted cities nearby."
            ),
        }

    @staticmethod
    def calculate_distance(
        lat1: float, lon1: float, lat2: float, lon2: float, unit: str = "miles"
    ) -> Dict[str, Any]:
        """
        Calculate distance between two points using Haversine formula

        Args:
            lat1, lon1: Coordinates of first point
            lat2, lon2: Coordinates of second point
            unit: Distance unit (miles, kilometers, meters)

        Returns:
            Dictionary with distance calculation results
        """
        distance_miles = LocationService.haversine_distance(lat1, lon1, lat2, lon2)
        distance_converted = LocationService.convert_distance(distance_miles, unit)

        return {
            "distance": round(distance_converted, 4),
            "unit": unit,
            "lat1": lat1,
            "lon1": lon1,
            "lat2": lat2,
            "lon2": lon2,
            "calculation_method": "Haversine",
        }

    @staticmethod
    def find_addresses_within_radius(
        db: Session,
        center_lat: float,
        center_lon: float,
        radius_miles: float,
        user_id: Optional[str] = None,
    ) -> list:
        """
        Find addresses within a specified radius using PostGIS spatial queries

        Args:
            db: Database session
            center_lat: Center latitude
            center_lon: Center longitude
            radius_miles: Search radius in miles
            user_id: Optional user filter

        Returns:
            List of addresses within the radius
        """
        # Convert miles to meters for PostGIS query
        radius_meters = radius_miles * 1609.34

        # Create point geometry for center
        center_point = f"POINT({center_lon} {center_lat})"

        # Build query
        query = db.query(UserAddress).filter(
            func.ST_DWithin(
                UserAddress.location,
                func.ST_GeomFromText(center_point, 4326),
                radius_meters,
            )
        )

        # Add user filter if specified
        if user_id:
            query = query.filter(UserAddress.user_id == user_id)

        return query.all()

    @staticmethod
    def create_address_point(latitude: float, longitude: float) -> str:
        """Create a PostGIS point from coordinates"""
        return f"POINT({longitude} {latitude})"

    @staticmethod
    def update_address_location(
        db: Session, address_id: str, latitude: float, longitude: float
    ) -> bool:
        """
        Update the location of an address

        Args:
            db: Database session
            address_id: Address ID to update
            latitude: New latitude
            longitude: New longitude

        Returns:
            True if successful, False otherwise
        """
        try:
            address = (
                db.query(UserAddress)
                .filter(UserAddress.address_id == address_id)
                .first()
            )
            if address:
                point = LocationService.create_address_point(latitude, longitude)
                address.location = text(f"ST_GeomFromText('{point}', 4326)")
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            print(f"Error updating address location: {e}")
            return False
