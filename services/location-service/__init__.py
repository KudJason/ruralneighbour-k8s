# Location Service Package
"""
Location Service - A microservice for managing addresses and location validation.

This package provides:
- Address management (CRUD operations)
- Location validation against business rules
- Distance calculations using Haversine formula
- Geographic search within radius
"""

__version__ = "1.0.0"
__author__ = "Location Service Team"

# Import main components for easy access
try:
    from app.main import app
    from app.core.config import settings
    from app.services.location_service import LocationService
    from app.crud.crud_address import address_crud
except ImportError:
    # Allow package to be imported even if dependencies are not available
    pass

__all__ = [
    "app",
    "settings", 
    "LocationService",
    "address_crud",
]
