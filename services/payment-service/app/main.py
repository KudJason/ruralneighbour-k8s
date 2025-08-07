from fastapi import FastAPI
from .api.v1.endpoints import payments, payment_methods

app = FastAPI(
    title="Payment Service",
    description="Payment processing and management service",
    version="1.0.0",
)

app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(
    payment_methods.router, prefix="/api/v1/payment-methods", tags=["payment-methods"]
)
