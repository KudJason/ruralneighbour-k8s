from fastapi import FastAPI
from .api.v1.endpoints import profiles, users
from .services.event_consumer import EventConsumer
import asyncio

app = FastAPI(title="User Service", version="1.0.0")

# Include routers
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["profiles"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])


# Start event consumer on startup
@app.on_event("startup")
async def startup_event():
    """Start the event consumer to listen for UserRegistered events"""
    consumer = EventConsumer()
    asyncio.create_task(consumer.start_consuming())


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}
