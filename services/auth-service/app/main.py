from fastapi import FastAPI

from .api.v1.endpoints import auth

app = FastAPI(title="Auth Service", version="1.0.0")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])


@app.get("/")
async def root():
    return {"message": "Auth Service is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/info")
async def info():
    return {
        "service": "Auth Service",
        "version": "1.0.0",
        "features": [
            "User authentication",
            "Token issuance",
            "Rate limiting",
        ],
        "configuration": {},
    }
