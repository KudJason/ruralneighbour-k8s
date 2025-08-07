from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    TIMESTAMP,
    func,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from ..db.base import Base
from enum import Enum


class PaymentMethodType(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_ACCOUNT = "bank_account"
    DIGITAL_WALLET = "digital_wallet"


class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"


class UserPaymentMethod(Base):
    __tablename__ = "user_payment_methods"

    method_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # References users table
    method_type = Column(String(50), nullable=False)
    provider = Column(String(50), nullable=False)
    provider_method_id = Column(
        String(255), nullable=False
    )  # External provider's method ID

    # Masked/Display Information (PCI compliant)
    display_name = Column(String(100))
    last_four = Column(String(4))  # Last 4 digits for cards
    brand = Column(String(50))  # e.g., "visa", "mastercard", "paypal"
    expiry_month = Column(Integer)  # For cards
    expiry_year = Column(Integer)  # For cards

    # Metadata
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    usage_history = relationship("PaymentMethodUsage", back_populates="payment_method")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "NOT (is_default = true AND is_active = false)",
            name="default_must_be_active",
        ),
    )


class PaymentMethodUsage(Base):
    __tablename__ = "payment_method_usage"

    usage_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    method_id = Column(
        UUID(as_uuid=True), ForeignKey("user_payment_methods.method_id"), nullable=False
    )
    payment_id = Column(
        UUID(as_uuid=True), ForeignKey("payments.payment_id"), nullable=False
    )
    used_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    payment_method = relationship("UserPaymentMethod", back_populates="usage_history")
    payment = relationship("Payment")  # Reference to existing Payment model
