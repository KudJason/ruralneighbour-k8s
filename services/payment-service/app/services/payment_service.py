import stripe
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from fastapi import HTTPException, status
from datetime import datetime

from ..models.payment import Payment, PaymentStatus, RefundStatus, PaymentMethod
from ..schemas.payment import (
    PaymentCreate,
    PaymentProcess,
    PaymentUpdate,
    PaymentHistoryCreate,
    RefundCreate,
    RefundUpdate,
)
from ..crud.crud_payment import (
    create_payment,
    get_payment_by_id,
    get_payments_by_user,
    get_payments_by_request,
    update_payment,
    create_payment_history,
    create_refund,
    update_refund,
    get_refund_by_id,
)
from .events import EventPublisher
from .paypal_service import PayPalService
from ..core.config import settings


# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class PaymentService:
    @staticmethod
    def process_payment(db: Session, payment_in: PaymentProcess):
        """Process a new payment through the appropriate payment provider"""
        if payment_in.payment_method == PaymentMethod.PAYPAL:
            return PayPalService.process_payment(db, payment_in)
        elif payment_in.payment_method in [
            PaymentMethod.STRIPE,
            PaymentMethod.CREDIT_CARD,
            PaymentMethod.DEBIT_CARD,
        ]:
            return PaymentService._process_stripe_payment(db, payment_in)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported payment method: {payment_in.payment_method}",
            )

    @staticmethod
    def _process_stripe_payment(db: Session, payment_in: PaymentProcess) -> Payment:
        """Process a new payment through Stripe"""
        try:
            # Create payment record
            payment_create = PaymentCreate(
                request_id=payment_in.request_id,
                payer_id=payment_in.payer_id,
                payee_id=payment_in.payee_id,
                amount=payment_in.amount,
                payment_method=payment_in.payment_method,
            )
            payment = create_payment(db, payment_create)

            # Update status to processing
            update_payment(
                db,
                payment.payment_id,
                PaymentUpdate(payment_status=PaymentStatus.PROCESSING),
            )

            # Process with Stripe
            try:
                charge = stripe.Charge.create(
                    amount=int(payment_in.amount * 100),  # Convert to cents
                    currency=settings.currency.lower(),
                    source=payment_in.payment_token,
                    description=f"Payment for request {payment_in.request_id}",
                )

                # Update payment with success status
                update_payment(
                    db,
                    payment.payment_id,
                    PaymentUpdate(
                        payment_status=PaymentStatus.SUCCESS, transaction_id=charge.id
                    ),
                )

                # Create payment history
                create_payment_history(
                    db,
                    PaymentHistoryCreate(
                        payment_id=payment.payment_id,
                        status=PaymentStatus.SUCCESS,
                        notes="Payment processed successfully",
                    ),
                )

                # Publish success event
                EventPublisher.publish_payment_processed(
                    payment_id=str(payment.payment_id),
                    request_id=str(payment_in.request_id),
                    amount=str(payment_in.amount),
                    status="success",
                )

                return get_payment_by_id(db, payment.payment_id)

            except stripe.error.CardError as e:
                # Handle card errors
                update_payment(
                    db,
                    payment.payment_id,
                    PaymentUpdate(payment_status=PaymentStatus.FAILED),
                )
                create_payment_history(
                    db,
                    PaymentHistoryCreate(
                        payment_id=payment.payment_id,
                        status=PaymentStatus.FAILED,
                        notes=f"Card error: {e.error.message}",
                    ),
                )

                EventPublisher.publish_payment_failed(
                    payment_id=str(payment.payment_id),
                    request_id=str(payment_in.request_id),
                    amount=str(payment_in.amount),
                    error_code="card_error",
                    error_message=e.error.message,
                )

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Payment failed: {e.error.message}",
                )

            except stripe.error.StripeError as e:
                # Handle other Stripe errors
                update_payment(
                    db,
                    payment.payment_id,
                    PaymentUpdate(payment_status=PaymentStatus.FAILED),
                )
                create_payment_history(
                    db,
                    PaymentHistoryCreate(
                        payment_id=payment.payment_id,
                        status=PaymentStatus.FAILED,
                        notes=f"Stripe error: {str(e)}",
                    ),
                )

                EventPublisher.publish_payment_failed(
                    payment_id=str(payment.payment_id),
                    request_id=str(payment_in.request_id),
                    amount=str(payment_in.amount),
                    error_code="stripe_error",
                    error_message=str(e),
                )

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Payment processing error",
                )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment processing failed: {str(e)}",
            )

    @staticmethod
    def get_payment_history(
        db: Session, user_id: UUID, page: int = 1, page_size: int = 20
    ) -> dict:
        """Get payment history for a user with pagination"""
        skip = (page - 1) * page_size
        payments = get_payments_by_user(db, user_id, skip=skip, limit=page_size)

        # Get total count
        total_count = db.query(Payment).filter(Payment.payer_id == user_id).count()

        return {
            "payments": payments,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    def process_refund(
        db: Session, payment_id: UUID, refund_in: RefundCreate, admin_id: UUID
    ) -> dict:
        """Process a refund for a payment (admin only)"""
        # Check if payment exists and was successful
        payment = get_payment_by_id(db, payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
            )

        if payment.payment_status != PaymentStatus.SUCCESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only refund successful payments",
            )

        # Check if refund amount is valid
        if refund_in.amount > payment.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund amount cannot exceed payment amount",
            )

        # Check for existing refunds
        from ..models.payment import Refund

        existing_refunds = (
            db.query(Refund).filter(Refund.payment_id == payment_id).all()
        )
        total_refunded = sum(
            refund.amount
            for refund in existing_refunds
            if refund.status == RefundStatus.COMPLETED
        )

        if total_refunded + refund_in.amount > payment.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total refund amount would exceed payment amount",
            )

        # Create refund record
        refund = create_refund(db, refund_in)

        # Update refund with admin approval
        update_refund(
            db,
            refund.refund_id,
            RefundUpdate(status=RefundStatus.APPROVED, approved_by=admin_id),
        )

        # Process refund with Stripe if transaction_id exists
        if payment.transaction_id:
            try:
                stripe_refund = stripe.Refund.create(
                    charge=payment.transaction_id,
                    amount=int(refund_in.amount * 100),  # Convert to cents
                )

                # Update refund as completed
                update_refund(
                    db,
                    refund.refund_id,
                    RefundUpdate(
                        status=RefundStatus.COMPLETED, completed_at=datetime.utcnow()
                    ),
                )

                # Publish refund event
                EventPublisher.publish_payment_refunded(
                    payment_id=str(payment_id),
                    request_id=str(payment.request_id),
                    amount=str(refund_in.amount),
                    refund_reason=refund_in.refund_reason,
                )

                return {
                    "refund_id": refund.refund_id,
                    "status": RefundStatus.COMPLETED,
                    "message": "Refund processed successfully",
                }

            except stripe.error.StripeError as e:
                # Update refund as failed
                update_refund(
                    db, refund.refund_id, RefundUpdate(status=RefundStatus.REJECTED)
                )

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Refund processing failed: {str(e)}",
                )
        else:
            # Manual refund (no Stripe transaction)
            update_refund(
                db,
                refund.refund_id,
                RefundUpdate(
                    status=RefundStatus.COMPLETED, completed_at=datetime.utcnow()
                ),
            )

            # Publish refund event
            EventPublisher.publish_payment_refunded(
                payment_id=str(payment_id),
                request_id=str(payment.request_id),
                amount=str(refund_in.amount),
                refund_reason=refund_in.refund_reason,
            )

            return {
                "refund_id": refund.refund_id,
                "status": RefundStatus.COMPLETED,
                "message": "Manual refund processed successfully",
            }

    @staticmethod
    def create_pending_payment(
        db: Session, request_id: UUID, payer_id: UUID, payee_id: UUID, amount: Decimal
    ) -> Payment:
        """Create a pending payment record when a service request is created"""
        payment_create = PaymentCreate(
            request_id=request_id,
            payer_id=payer_id,
            payee_id=payee_id,
            amount=amount,
            payment_method=PaymentMethod.CREDIT_CARD,  # Default method
        )
        payment = create_payment(db, payment_create)

        # Create initial history record
        create_payment_history(
            db,
            PaymentHistoryCreate(
                payment_id=payment.payment_id,
                status=PaymentStatus.PENDING,
                notes="Payment record created for service request",
            ),
        )

        return payment
