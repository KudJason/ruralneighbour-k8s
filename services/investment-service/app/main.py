import os

from fastapi import FastAPI

from app.api.v1.endpoints import investments
from app.db.base import Base, engine


# Create tables only if not in testing environment
if os.getenv("TESTING") != "true":
    Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Investment Service",
    description="Service for managing investment opportunities",
    version="1.0.0",
)


app.include_router(investments.router, prefix="/api/v1", tags=["investments"])


@app.get("/")
async def root():
    return {"message": "Investment Service is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}








