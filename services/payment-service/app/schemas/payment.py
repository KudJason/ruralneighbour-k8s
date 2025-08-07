from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from ..models.payment import PaymentStatus, PaymentMethod, RefundStatus


class PaymentBase(BaseModel):
    request_id: UUID
    payer_id: UUID
    payee_id: UUID
    amount: Decimal = Field(..., ge=0.01)
    payment_method: PaymentMethod


class PaymentCreate(PaymentBase):
    pass


class PaymentProcess(PaymentBase):
    payment_token: str  # Payment provider token (e.g., Stripe token)


class PaymentUpdate(BaseModel):
    payment_status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = None


class PaymentOut(PaymentBase):
    payment_id: UUID
    payment_status: PaymentStatus
    transaction_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentHistoryBase(BaseModel):
    status: PaymentStatus
    notes: Optional[str] = None


class PaymentHistoryCreate(PaymentHistoryBase):
    payment_id: UUID


class PaymentHistoryOut(PaymentHistoryBase):
    history_id: UUID
    payment_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class RefundBase(BaseModel):
    payment_id: UUID
    amount: Decimal = Field(..., ge=0.01)
    refund_reason: str


class RefundCreate(RefundBase):
    pass


class RefundUpdate(BaseModel):
    status: Optional[RefundStatus] = None
    approved_by: Optional[UUID] = None
    completed_at: Optional[datetime] = None


class RefundOut(RefundBase):
    refund_id: UUID
    status: RefundStatus
    approved_by: Optional[UUID] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentHistoryResponse(BaseModel):
    payments: List[PaymentOut]
    total_count: int
    page: int
    page_size: int


class PaymentProcessResponse(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    transaction_id: Optional[str] = None
    message: str


class RefundResponse(BaseModel):
    refund_id: UUID
    status: RefundStatus
    message: str
