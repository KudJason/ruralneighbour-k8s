from pydantic import BaseModel, Field, validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from ..models.payment_method import PaymentMethodType, PaymentProvider


class PaymentMethodCreate(BaseModel):
    method_type: PaymentMethodType
    provider: PaymentProvider
    provider_token: str = Field(
        ..., description="Provider-specific token (e.g., Stripe payment method token)"
    )
    display_name: Optional[str] = None
    set_as_default: bool = False

    class Config:
        use_enum_values = True


class PaymentMethodUpdate(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        use_enum_values = True


class PaymentMethodOut(BaseModel):
    method_id: UUID
    method_type: str
    provider: str
    display_name: Optional[str]
    last_four: Optional[str]
    brand: Optional[str]
    expiry_month: Optional[int]
    expiry_year: Optional[int]
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentMethodListResponse(BaseModel):
    payment_methods: List[PaymentMethodOut]
    total_count: int


class QuickPaymentRequest(BaseModel):
    request_id: UUID
    payee_id: UUID
    amount: str = Field(..., pattern=r"^\d+\.\d{2}$")
    method_id: UUID
    description: Optional[str] = None

    @validator("amount")
    def validate_amount(cls, v):
        try:
            amount = float(v)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            if amount > 999999.99:
                raise ValueError("Amount too large")
            return v
        except ValueError as e:
            raise ValueError(f"Invalid amount: {e}")


class SavedMethodPaymentRequest(BaseModel):
    request_id: UUID
    payer_id: UUID
    payee_id: UUID
    amount: str = Field(..., pattern=r"^\d+\.\d{2}$")
    payment_method: str = Field(..., description="Must be 'saved_method'")
    saved_method_id: UUID
    save_method: Optional[bool] = False  # For future use

    @validator("payment_method")
    def validate_payment_method(cls, v):
        if v != "saved_method":
            raise ValueError('payment_method must be "saved_method"')
        return v

    @validator("amount")
    def validate_amount(cls, v):
        try:
            amount = float(v)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            if amount > 999999.99:
                raise ValueError("Amount too large")
            return v
        except ValueError as e:
            raise ValueError(f"Invalid amount: {e}")


class SetDefaultPaymentMethodRequest(BaseModel):
    method_id: UUID


class PaymentMethodUsageOut(BaseModel):
    usage_id: UUID
    method_id: UUID
    payment_id: UUID
    used_at: datetime

    class Config:
        from_attributes = True
