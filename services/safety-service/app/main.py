import os

# ensure models are imported
import app.db.init_db
from app.api.v1.endpoints import disputes, metrics, safety
from app.db.base import Base, engine
from fastapi import FastAPI

if os.getenv("TESTING") != "true":
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="Safety & Dispute Service", version="1.0.0")

app.include_router(disputes.router, prefix="/api/v1", tags=["disputes"])
app.include_router(safety.router, prefix="/api/v1", tags=["safety"])
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])


@app.get("/")
async def root():
    return {"message": "Safety & Dispute Service is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

