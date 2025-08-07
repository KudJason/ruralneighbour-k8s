from fastapi import FastAPI
from .api.v1.endpoints import auth

app = FastAPI()

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
