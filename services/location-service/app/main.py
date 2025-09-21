from fastapi import FastAPI
from app.api.v1.endpoints import addresses, locations
from app.models import saved_location  # ensure model is imported for table creation
from app.core.config import settings
from app.db.base import engine, Base

# Import models after creating Base to avoid circular imports
import app.db.init_db

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Location Service",
    description="Service for managing addresses and location validation",
    version="1.0.0",
)

# Include routers
app.include_router(addresses.router, prefix="/api/v1", tags=["addresses"])
app.include_router(locations.router, prefix="/api/v1", tags=["locations"])


@app.get("/")
async def root():
    return {"message": "Location Service is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/info")
async def info():
    """Get service information and configuration"""
    return {
        "service": "Location Service",
        "version": "1.0.0",
        "features": [
            "Address Management (CRUD)",
            "Location Validation",
            "Distance Calculation (Haversine)",
            "PostGIS Spatial Queries",
            "Performance Monitoring",
        ],
        "configuration": {
            "restricted_city_population_threshold": settings.RESTRICTED_CITY_POPULATION_THRESHOLD,
            "restricted_area_radius_miles": settings.RESTRICTED_AREA_RADIUS_MILES,
            "max_query_time_ms": settings.MAX_QUERY_TIME_MS,
        },
    }
