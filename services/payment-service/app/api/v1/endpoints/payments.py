from typing import Optional
from uuid import UUID

import stripe
from app.db.session import get_db
from app.schemas.payment import (
    PaymentHistoryResponse,
    PaymentProcess,
    PaymentProcessResponse,
    RefundCreate,
    RefundResponse,
)
from app.schemas.payment_method import (
    PaymentMethodCreate,
    PaymentMethodOut,
    PaymentMethodUpdate,
)
from app.services.payment_method_service import PaymentMethodService
from app.services.payment_service import PaymentService
from app.services.paypal_service import PayPalService
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter()


def get_current_user_id() -> UUID:
    """Mock current user id provider, aligned with payment_methods module."""
    from uuid import uuid4

    return uuid4()


class StripePaymentIntentIn(BaseModel):
    amount: int = Field(
        ..., ge=1, description="Amount in smallest currency unit (e.g. cents)"
    )
    currency: str = Field(..., description="ISO currency code, e.g. 'usd'")
    description: Optional[str] = None
    payment_method_id: Optional[str] = None


class StripePaymentIntentOut(BaseModel):
    id: str
    status: str
    client_secret: Optional[str] = None
    amount: int
    currency: str
    requires_action: bool = False


class StripeAttachMethodIn(BaseModel):
    payment_method_id: str
    make_default: Optional[bool] = False


class StripeAttachMethodOut(BaseModel):
    id: str
    type: Optional[str] = None
    last_four: Optional[str] = None
    is_default: bool = False


class PayPalCreateOrderIn(BaseModel):
    amount: int = Field(..., ge=1)
    currency: str
    description: Optional[str] = None
    return_url: str
    cancel_url: str


class PayPalCreateOrderOut(BaseModel):
    id: str
    status: str
    approve_url: Optional[str] = None


@router.post("/process", response_model=PaymentProcessResponse)
def process_payment(payment_in: PaymentProcess, db: Session = Depends(get_db)):
    """
    Process a new payment
    """
    try:
        payment = PaymentService.process_payment(db, payment_in)
        return PaymentProcessResponse(
            payment_id=payment.payment_id,
            status=payment.payment_status,
            transaction_id=payment.transaction_id,
            message="Payment processed successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment processing failed: {str(e)}",
        )


@router.get("/history", response_model=PaymentHistoryResponse)
def get_payment_history(
    user_id: UUID = Query(..., description="User ID to get payment history for"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    db: Session = Depends(get_db),
):
    """
    Get payment history for a user with pagination
    """
    try:
        result = PaymentService.get_payment_history(db, user_id, page, page_size)
        return PaymentHistoryResponse(
            payments=result["payments"],
            total_count=result["total_count"],
            page=result["page"],
            page_size=result["page_size"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment history: {str(e)}",
        )


@router.post("/{payment_id}/refund", response_model=RefundResponse)
def process_refund(
    payment_id: UUID,
    refund_in: RefundCreate,
    admin_id: UUID = Query(..., description="Admin ID processing the refund"),
    db: Session = Depends(get_db),
):
    """
    Process a refund for a payment (admin only)
    """
    try:
        result = PaymentService.process_refund(db, payment_id, refund_in, admin_id)
        return RefundResponse(
            refund_id=result["refund_id"],
            status=result["status"],
            message=result["message"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refund processing failed: {str(e)}",
        )


@router.post("/paypal/execute")
def execute_paypal_payment(
    payment_id: str = Query(..., description="Payment ID"),
    payer_id: str = Query(..., description="PayPal Payer ID"),
    db: Session = Depends(get_db),
):
    """Execute a PayPal payment after user approval"""
    try:
        payment = PayPalService.execute_payment(db, payment_id, payer_id)
        return PaymentProcessResponse(
            payment_id=payment.payment_id,
            status=payment.payment_status,
            transaction_id=payment.transaction_id,
            message="PayPal payment executed successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PayPal payment execution failed: {str(e)}",
        )


@router.post("/paypal/cancel")
def cancel_paypal_payment(
    payment_id: str = Query(..., description="Payment ID"),
    db: Session = Depends(get_db),
):
    """Cancel a PayPal payment"""
    try:
        payment = PayPalService.cancel_payment(db, payment_id)
        return PaymentProcessResponse(
            payment_id=payment.payment_id,
            status=payment.payment_status,
            transaction_id=payment.transaction_id,
            message="PayPal payment cancelled",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PayPal payment cancellation failed: {str(e)}",
        )


# --- Payment Methods compatibility endpoints (under /payments prefix) ---


class MethodCompatCreateIn(BaseModel):
    type: str
    details: dict
    is_default: Optional[bool] = False


@router.post("/methods")
def payments_create_method(
    body: MethodCompatCreateIn,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Compatibility alias for creating payment method via /api/v1/payments/methods
    Maps { type, details, is_default } to internal PaymentMethodCreate.
    """
    try:
        raw_type = (body.type or "").lower()
        if raw_type in ("card", "credit_card", "stripe"):
            method_type = "credit_card"
            provider = "stripe"
        elif raw_type in ("debit_card",):
            method_type = "debit_card"
            provider = "stripe"
        elif raw_type in ("paypal",):
            method_type = "paypal"
            provider = "paypal"
        else:
            method_type = raw_type
            provider = raw_type

        provider_token = (
            body.details.get("payment_method_id") or body.details.get("token") or ""
        )

        create_in = PaymentMethodCreate(
            method_type=method_type,
            provider=provider,
            provider_token=provider_token,
            display_name=body.details.get("label") or body.details.get("brand"),
            set_as_default=bool(body.is_default),
        )
        result = PaymentMethodService.save_payment_method(
            db, current_user_id, create_in
        )
        return {
            "is_default": bool(getattr(result, "is_default", body.is_default or False))
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create payment method: {str(e)}",
        )


class MethodCompatUpdateIn(BaseModel):
    details: Optional[dict] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


@router.put("/methods/{method_id}")
def payments_update_method(
    method_id: UUID,
    body: MethodCompatUpdateIn,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Compatibility alias for updating method via /api/v1/payments/methods/{id}
    Supports { details, is_default, is_active } mapping.
    """
    try:
        updated = None
        if body.details is not None:
            display = body.details.get("label") or body.details.get("brand")
            updated = PaymentMethodService.update_payment_method(
                db,
                method_id,
                current_user_id,
                PaymentMethodUpdate(display_name=display),
            )
        if body.is_default is True:
            updated = PaymentMethodService.set_default_payment_method(
                db, method_id, current_user_id
            )
        if body.is_active is not None and updated is None:
            updated = PaymentMethodService.update_payment_method(
                db,
                method_id,
                current_user_id,
                PaymentMethodUpdate(is_active=body.is_active),
            )
        if updated is None:
            updated = PaymentMethodService.update_payment_method(
                db, method_id, current_user_id, PaymentMethodUpdate()
            )
        return {"is_default": bool(getattr(updated, "is_default", False))}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update payment method: {str(e)}",
        )


# --- Transactions compatibility endpoint ---


class TransactionCreateIn(BaseModel):
    amount: int = Field(..., ge=1)
    currency: str
    description: Optional[str] = None
    payment_method_id: str
    service_request_id: Optional[str] = None
    type: Optional[str] = Field(default="payment")


class TransactionOut(BaseModel):
    id: str
    type: str
    status: str
    amount: int
    currency: str


@router.post("/transactions", response_model=TransactionOut)
def create_transaction(body: TransactionCreateIn):
    """
    Create a payment transaction using Stripe by default.
    If type is 'payment', confirm immediately with provided payment_method_id.
    """
    if body.type not in (None, "payment"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported transaction type: {body.type}",
        )
    try:
        intent = stripe.PaymentIntent.create(
            amount=body.amount,
            currency=body.currency.lower(),
            description=body.description,
            payment_method=body.payment_method_id,
            confirm=True,
            automatic_payment_methods={"enabled": True},
        )
        return TransactionOut(
            id=intent.id,
            type="payment",
            status=intent.status,
            amount=int(intent.amount),
            currency=intent.currency,
        )
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Stripe error: {str(e)}",
        )


# --- Compatibility/Gateway-style endpoints ---


@router.post("/stripe/payment-intent", response_model=StripePaymentIntentOut)
def create_stripe_payment_intent(
    body: StripePaymentIntentIn,
):
    """
    Create a Stripe PaymentIntent, optionally confirm if payment_method_id provided.
    Does not persist to local DB; acts as a thin gateway for the frontend.
    """
    try:
        intent = stripe.PaymentIntent.create(
            amount=body.amount,
            currency=body.currency.lower(),
            description=body.description,
            payment_method=body.payment_method_id,
            confirm=True if body.payment_method_id else False,
            automatic_payment_methods={"enabled": True},
        )
        requires_action = intent.status == "requires_action"
        return StripePaymentIntentOut(
            id=intent.id,
            status=intent.status,
            client_secret=getattr(intent, "client_secret", None),
            amount=int(intent.amount),
            currency=intent.currency,
            requires_action=requires_action,
        )
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}",
        )


@router.post("/stripe/attach-method", response_model=StripeAttachMethodOut)
def stripe_attach_method(
    body: StripeAttachMethodIn,
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Attach a Stripe payment method to a customer bound to current user.
    For MVP, create a customer if not exists (no persistence layer here).
    """
    try:
        customer = stripe.Customer.create(metadata={"user_id": str(current_user_id)})
        pm = stripe.PaymentMethod.attach(
            body.payment_method_id,
            customer=customer.id,
        )
        if body.make_default:
            stripe.Customer.modify(
                customer.id,
                invoice_settings={"default_payment_method": pm.id},
            )
        last4 = None
        pm_type = getattr(pm, "type", None)
        if pm_type == "card":
            last4 = getattr(pm.card, "last4", None)
        return StripeAttachMethodOut(
            id=pm.id,
            type=pm_type,
            last_four=last4,
            is_default=bool(body.make_default),
        )
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}",
        )


@router.post("/paypal/create-order", response_model=PayPalCreateOrderOut)
def paypal_create_order(body: PayPalCreateOrderIn):
    """
    Create a PayPal payment (v1 Payments) and return approval URL.
    Thin gateway; no local DB persistence.
    """
    try:
        from app.services.paypal_service import paypalrestsdk

        payment = paypalrestsdk.Payment(
            {
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": body.return_url,
                    "cancel_url": body.cancel_url,
                },
                "transactions": [
                    {
                        "amount": {
                            "total": str(body.amount / 100),
                            "currency": body.currency,
                        },
                        "description": body.description or "",
                    }
                ],
            }
        )
        if payment.create():
            approve_url = None
            for link in payment.links:
                if link.rel == "approval_url":
                    approve_url = link.href
                    break
            return PayPalCreateOrderOut(
                id=payment.id, status="CREATED", approve_url=approve_url
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PayPal error: {payment.error}",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PayPal create order failed: {str(e)}",
        )


class PayPalCaptureIn(BaseModel):
    payer_id: str = Field(
        ..., description="PayPal Payer ID returned from approval redirect"
    )


@router.post("/paypal/capture/{order_id}")
def paypal_capture_order(order_id: str, body: PayPalCaptureIn):
    """
    Capture a PayPal payment created by create-order.
    For v1 Payments API, execute with payer_id.
    """
    try:
        from app.services.paypal_service import paypalrestsdk

        payment = paypalrestsdk.Payment.find(order_id)
        if payment.execute({"payer_id": body.payer_id}):
            # Return a minimal normalized payload
            return {
                "id": payment.id,
                "status": getattr(payment, "state", "COMPLETED").upper(),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PayPal capture error: {payment.error}",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PayPal capture failed: {str(e)}",
        )


# ========== Frontend Compatibility Endpoints ==========


@router.get("/methods", response_model=PaymentMethodListResponse)
def get_payment_methods_for_frontend(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Get all payment methods for the current user (frontend compatibility)
    """
    try:
        result = PaymentMethodService.get_user_payment_methods(
            db, current_user_id, skip, limit
        )
        return PaymentMethodListResponse(
            payment_methods=result["payment_methods"],
            total_count=result["total_count"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment methods: {str(e)}",
        )


@router.get("/methods/{method_id}", response_model=PaymentMethodOut)
def get_payment_method_for_frontend(
    method_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Get a specific payment method (frontend compatibility)
    """
    try:
        result = PaymentMethodService.get_payment_method(db, method_id, current_user_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment method: {str(e)}",
        )


@router.delete("/methods/{method_id}")
def delete_payment_method_for_frontend(
    method_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Delete a payment method (frontend compatibility)
    """
    try:
        PaymentMethodService.delete_payment_method(db, method_id, current_user_id)
        return {"message": "Payment method deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete payment method: {str(e)}",
        )


@router.get("/transactions", response_model=PaymentHistoryResponse)
def get_transactions_for_frontend(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Get payment history for the current user (frontend compatibility)
    """
    try:
        result = PaymentService.get_payment_history(
            db, current_user_id, page, page_size
        )
        return PaymentHistoryResponse(
            payments=result["payments"],
            total_count=result["total_count"],
            page=result["page"],
            page_size=result["page_size"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment history: {str(e)}",
        )


@router.get("/transactions/{transaction_id}", response_model=TransactionOut)
def get_transaction_for_frontend(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Get a specific transaction (frontend compatibility)
    """
    try:
        # This would need to be implemented in PaymentService
        # For now, return a mock response
        return TransactionOut(
            id=transaction_id,
            type="payment",
            status="completed",
            amount=1000,
            currency="usd",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transaction: {str(e)}",
        )


@router.put("/transactions/{transaction_id}", response_model=TransactionOut)
def update_transaction_for_frontend(
    transaction_id: str,
    status: str = Query(..., description="New status"),
    notes: str = Query(None, description="Notes"),
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Update a transaction (frontend compatibility)
    """
    try:
        # This would need to be implemented in PaymentService
        # For now, return a mock response
        return TransactionOut(
            id=transaction_id,
            type="payment",
            status=status,
            amount=1000,
            currency="usd",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update transaction: {str(e)}",
        )
