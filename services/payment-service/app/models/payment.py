from sqlalchemy import Column, String, DECIMAL, TIMESTAMP, func, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from ..db.base import Base
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    PAYPAL = "paypal"
    STRIPE = "stripe"


class RefundStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    COMPLETED = "completed"
    REJECTED = "rejected"


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), nullable=False)
    payer_id = Column(UUID(as_uuid=True), nullable=False)
    payee_id = Column(UUID(as_uuid=True), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    payment_status = Column(String(50), default=PaymentStatus.PENDING)
    payment_method = Column(String(50), nullable=False)
    transaction_id = Column(String(255))  # External payment provider's transaction ID
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    payment_history = relationship("PaymentHistory", back_populates="payment")
    refunds = relationship("Refund", back_populates="payment")


class PaymentHistory(Base):
    __tablename__ = "payment_history"

    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(
        UUID(as_uuid=True), ForeignKey("payments.payment_id"), nullable=False
    )
    status = Column(String(50), nullable=False)
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    payment = relationship("Payment", back_populates="payment_history")


class Refund(Base):
    __tablename__ = "refunds"

    refund_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(
        UUID(as_uuid=True), ForeignKey("payments.payment_id"), nullable=False
    )
    amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(String(50), default=RefundStatus.PENDING)
    refund_reason = Column(Text, nullable=False)
    approved_by = Column(UUID(as_uuid=True))  # Admin who approved
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True))

    # Relationships
    payment = relationship("Payment", back_populates="refunds")
