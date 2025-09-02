from fastapi import FastAPI

from .api.v1.endpoints import payment_methods, payments

app = FastAPI(
    title="Payment Service",
    description="Payment processing and management service",
    version="1.0.0",
)

app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(
    payment_methods.router, prefix="/api/v1/payment-methods", tags=["payment-methods"]
)


@app.get("/")
async def root():
    return {"message": "Payment Service is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/info")
async def info():
    return {
        "service": "Payment Service",
        "version": "1.0.0",
        "features": [
            "Payment execution",
            "Payment methods",
            "Event publishing",
        ],
        "configuration": {},
    }
