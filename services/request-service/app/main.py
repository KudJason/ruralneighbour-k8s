import os

from app.api.v1.endpoints import service_requests
from app.core.config import settings
from app.db.base import Base, engine
from fastapi import FastAPI

# Create tables only if not in testing environment
if os.getenv("TESTING") != "true":
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Request Service",
    description="Service for managing service requests",
    version="1.0.0",
)

# Include routers
app.include_router(service_requests.router, prefix="/api/v1", tags=["service_requests"])


@app.get("/")
async def root():
    return {"message": "Request Service is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/info")
async def info():
    return {
        "service": "Request Service",
        "version": "1.0.0",
        "features": [
            "Service request lifecycle",
            "Provider matching",
        ],
        "configuration": {},
    }
