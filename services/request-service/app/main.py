from fastapi import FastAPI
import asyncio
import threading
from contextlib import asynccontextmanager
from app.api.v1.endpoints import requests, providers
from app.core.config import settings
from app.db.base import engine, Base
from app.services.event_consumer import EventConsumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application"""
    # Create database tables
    Base.metadata.create_all(bind=engine)

    consumer = EventConsumer()

    def run_consumer():
        asyncio.run(consumer.start_consuming())

    # Start consumer in a separate thread
    consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    consumer_thread.start()

    yield

    # Cleanup if needed
    consumer.stop()


app = FastAPI(
    title="Request Service",
    description="Service for managing service requests",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(requests.router, prefix="/api/v1/requests", tags=["requests"])

app.include_router(providers.router, prefix="/api/v1/providers", tags=["providers"])


@app.get("/")
async def root():
    return {"message": "Request Service is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
