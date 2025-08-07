import paypalrestsdk
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from fastapi import HTTPException, status
from datetime import datetime

from ..core.config import settings
from ..models.payment import Payment, PaymentStatus
from ..schemas.payment import PaymentProcess, PaymentUpdate, PaymentHistoryCreate
from ..crud.crud_payment import (
    create_payment,
    update_payment,
    create_payment_history,
    get_payment_by_id,
)
from .events import EventPublisher

# Initialize PayPal SDK
paypalrestsdk.configure(
    {
        "mode": settings.paypal_mode,
        "client_id": settings.paypal_client_id,
        "client_secret": settings.paypal_client_secret,
    }
)


class PayPalService:
    @staticmethod
    def process_payment(db: Session, payment_in: PaymentProcess) -> Dict[str, Any]:
        """Process a payment through PayPal - returns approval URL for user redirect"""
        try:
            # Create payment record
            from ..schemas.payment import PaymentCreate

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

            # Create PayPal payment
            paypal_payment = paypalrestsdk.Payment(
                {
                    "intent": "sale",
                    "payer": {"payment_method": "paypal"},
                    "redirect_urls": {
                        "return_url": f"{settings.base_url}/api/v1/payments/paypal/execute?payment_id={payment.payment_id}",
                        "cancel_url": f"{settings.base_url}/api/v1/payments/paypal/cancel?payment_id={payment.payment_id}",
                    },
                    "transactions": [
                        {
                            "item_list": {
                                "items": [
                                    {
                                        "name": f"Payment for request {payment_in.request_id}",
                                        "sku": str(payment_in.request_id),
                                        "price": str(payment_in.amount),
                                        "currency": settings.currency,
                                        "quantity": 1,
                                    }
                                ]
                            },
                            "amount": {
                                "total": str(payment_in.amount),
                                "currency": settings.currency,
                            },
                            "description": f"Payment for request {payment_in.request_id}",
                        }
                    ],
                }
            )

            if paypal_payment.create():
                # Update payment with PayPal payment ID
                update_payment(
                    db,
                    payment.payment_id,
                    PaymentUpdate(transaction_id=paypal_payment.id),
                )

                # Create payment history
                create_payment_history(
                    db,
                    PaymentHistoryCreate(
                        payment_id=payment.payment_id,
                        status=PaymentStatus.PROCESSING,
                        notes="PayPal payment created, waiting for user approval",
                    ),
                )

                # Find approval URL
                approval_url = None
                for link in paypal_payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break

                return {
                    "payment_id": str(payment.payment_id),
                    "paypal_payment_id": paypal_payment.id,
                    "approval_url": approval_url,
                    "status": "created",
                }
            else:
                # Handle PayPal creation error
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
                        notes=f"PayPal payment creation failed: {paypal_payment.error}",
                    ),
                )

                EventPublisher.publish_payment_failed(
                    payment_id=str(payment.payment_id),
                    request_id=str(payment_in.request_id),
                    amount=str(payment_in.amount),
                    error_code="paypal_error",
                    error_message=str(paypal_payment.error),
                )

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"PayPal payment creation failed: {paypal_payment.error}",
                )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PayPal payment processing failed: {str(e)}",
            )

    @staticmethod
    def execute_payment(db: Session, payment_id: str, payer_id: str) -> Payment:
        """Execute a PayPal payment after user approval"""
        try:
            payment = get_payment_by_id(db, UUID(payment_id))
            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found")

            # Execute the PayPal payment
            paypal_payment = paypalrestsdk.Payment.find(payment.transaction_id)
            if paypal_payment.execute({"payer_id": payer_id}):
                # Update payment status to success
                update_payment(
                    db,
                    payment.payment_id,
                    PaymentUpdate(payment_status=PaymentStatus.SUCCESS),
                )
                create_payment_history(
                    db,
                    PaymentHistoryCreate(
                        payment_id=payment.payment_id,
                        status=PaymentStatus.SUCCESS,
                        notes="PayPal payment executed successfully",
                    ),
                )

                # Publish success event
                EventPublisher.publish_payment_processed(
                    payment_id=str(payment.payment_id),
                    request_id=str(payment.request_id),
                    amount=str(payment.amount),
                    status="success",
                )

                return get_payment_by_id(db, payment.payment_id)
            else:
                # Handle execution error
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
                        notes=f"PayPal payment execution failed: {paypal_payment.error}",
                    ),
                )

                EventPublisher.publish_payment_failed(
                    payment_id=str(payment.payment_id),
                    request_id=str(payment.request_id),
                    amount=str(payment.amount),
                    error_code="paypal_execution_error",
                    error_message=str(paypal_payment.error),
                )

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"PayPal payment execution failed: {paypal_payment.error}",
                )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PayPal payment execution failed: {str(e)}",
            )

    @staticmethod
    def cancel_payment(db: Session, payment_id: str) -> Payment:
        """Cancel a PayPal payment"""
        try:
            payment = get_payment_by_id(db, UUID(payment_id))
            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found")

            # Update payment status to cancelled
            update_payment(
                db,
                payment.payment_id,
                PaymentUpdate(payment_status=PaymentStatus.CANCELLED),
            )
            create_payment_history(
                db,
                PaymentHistoryCreate(
                    payment_id=payment.payment_id,
                    status=PaymentStatus.CANCELLED,
                    notes="PayPal payment cancelled by user",
                ),
            )

            return get_payment_by_id(db, payment.payment_id)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PayPal payment cancellation failed: {str(e)}",
            )
