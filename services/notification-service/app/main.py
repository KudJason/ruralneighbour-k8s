from fastapi import FastAPI
from app.api.v1.endpoints import messages, notifications, events
from app.core.config import settings
from app.db.base import engine, Base
import os

# Import models after creating Base to avoid circular imports
import app.db.init_db

# Create tables only if not in testing environment
if os.getenv("TESTING") != "true":
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Notification Service",
    description="Service for managing notifications and messages",
    version="1.0.0",
)

# Include routers
app.include_router(messages.router, prefix="/api/v1", tags=["messages"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
app.include_router(events.router, prefix="/api/v1", tags=["events"])


@app.get("/")
async def root():
    return {"message": "Notification Service is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/info")
async def info():
    """Get service information and configuration"""
    return {
        "service": "Notification Service",
        "version": "1.0.0",
        "features": [
            "Message Management (CRUD)",
            "Notification Management (CRUD)",
            "Event-Driven Notifications",
            "Multi-channel Delivery (Email, Push, In-App)",
            "Real-time Messaging",
            "Notification Retention Policy",
        ],
        "configuration": {
            "notification_retention_days": settings.notification_retention_days,
            "max_retry_attempts": settings.max_retry_attempts,
        },
    }
