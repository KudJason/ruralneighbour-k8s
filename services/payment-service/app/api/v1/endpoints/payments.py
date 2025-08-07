from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.schemas.payment import (
    PaymentProcess,
    PaymentProcessResponse,
    PaymentHistoryResponse,
    RefundCreate,
    RefundResponse,
)
from app.services.payment_service import PaymentService
from app.services.paypal_service import PayPalService
from app.db.session import get_db

router = APIRouter()


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
