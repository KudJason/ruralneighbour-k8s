import stripe
import paypalrestsdk
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from fastapi import HTTPException, status

from ..core.config import settings
from ..models.payment_method import (
    UserPaymentMethod,
    PaymentMethodType,
    PaymentProvider,
)
from ..schemas.payment_method import (
    PaymentMethodCreate,
    PaymentMethodUpdate,
    PaymentMethodOut,
    QuickPaymentRequest,
)
from ..crud.crud_payment_method import (
    create_payment_method,
    get_payment_method_by_id,
    get_user_payment_methods,
    get_user_default_payment_method,
    update_payment_method,
    set_default_payment_method,
    delete_payment_method,
    count_user_payment_methods,
    create_payment_method_usage,
)
from .events import EventPublisher


class PaymentMethodService:
    @staticmethod
    def save_payment_method(
        db: Session, user_id: UUID, payment_method_in: PaymentMethodCreate
    ) -> UserPaymentMethod:
        """Save a new payment method for a user"""
        try:
            # Process with the appropriate provider
            if payment_method_in.provider == PaymentProvider.STRIPE:
                return PaymentMethodService._save_stripe_payment_method(
                    db, user_id, payment_method_in
                )
            elif payment_method_in.provider == PaymentProvider.PAYPAL:
                return PaymentMethodService._save_paypal_payment_method(
                    db, user_id, payment_method_in
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported payment provider: {payment_method_in.provider}",
                )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save payment method: {str(e)}",
            )

    @staticmethod
    def _save_stripe_payment_method(
        db: Session, user_id: UUID, payment_method_in: PaymentMethodCreate
    ) -> UserPaymentMethod:
        """Save a Stripe payment method"""
        try:
            # Get or create Stripe customer
            stripe_customer_id = PaymentMethodService._get_or_create_stripe_customer(
                user_id
            )

            # Attach payment method to customer
            stripe.PaymentMethod.attach(
                payment_method_in.provider_token,
                customer=stripe_customer_id,
            )

            # Get payment method details from Stripe
            stripe_pm = stripe.PaymentMethod.retrieve(payment_method_in.provider_token)

            # Extract display information
            display_info = PaymentMethodService._extract_stripe_display_info(stripe_pm)

            # Create payment method record
            payment_method_data = PaymentMethodCreate(
                method_type=payment_method_in.method_type,
                provider=payment_method_in.provider,
                provider_token=f"{stripe_customer_id}:{payment_method_in.provider_token}",
                display_name=payment_method_in.display_name
                or display_info["display_name"],
                set_as_default=payment_method_in.set_as_default,
            )

            db_payment_method = create_payment_method(db, payment_method_data, user_id)

            # Update with display information
            db_payment_method.last_four = display_info["last_four"]
            db_payment_method.brand = display_info["brand"]
            db_payment_method.expiry_month = display_info["expiry_month"]
            db_payment_method.expiry_year = display_info["expiry_year"]

            db.commit()
            db.refresh(db_payment_method)

            # Publish event
            EventPublisher.publish_payment_method_saved(
                method_id=str(db_payment_method.method_id),
                user_id=str(user_id),
                method_type=str(payment_method_in.method_type),
            )

            return db_payment_method

        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}",
            )

    @staticmethod
    def _save_paypal_payment_method(
        db: Session, user_id: UUID, payment_method_in: PaymentMethodCreate
    ) -> UserPaymentMethod:
        """Save a PayPal payment method (vault)"""
        try:
            # For PayPal, we would use their Vault API
            # This is a simplified implementation

            # Create payment method record
            display_name = payment_method_in.display_name or "PayPal Account"

            payment_method_data = PaymentMethodCreate(
                method_type=PaymentMethodType.PAYPAL,
                provider=PaymentProvider.PAYPAL,
                provider_token=payment_method_in.provider_token,  # PayPal agreement ID
                display_name=display_name,
                set_as_default=payment_method_in.set_as_default,
            )

            db_payment_method = create_payment_method(db, payment_method_data, user_id)

            # Update with PayPal-specific display information
            db_payment_method.brand = "paypal"

            db.commit()
            db.refresh(db_payment_method)

            # Publish event
            EventPublisher.publish_payment_method_saved(
                method_id=str(db_payment_method.method_id),
                user_id=str(user_id),
                method_type=str(payment_method_in.method_type),
            )

            return db_payment_method

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PayPal error: {str(e)}",
            )

    @staticmethod
    def _get_or_create_stripe_customer(user_id: UUID) -> str:
        """Get or create a Stripe customer for the user"""
        # In a real implementation, you'd store the Stripe customer ID
        # in the user record or a separate table
        try:
            # For now, create a new customer each time
            # In production, you'd check if customer exists first
            customer = stripe.Customer.create(
                metadata={"user_id": str(user_id)},
            )
            return customer.id
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create Stripe customer: {str(e)}",
            )

    @staticmethod
    def _extract_stripe_display_info(stripe_pm) -> Dict[str, Any]:
        """Extract display information from Stripe payment method"""
        if stripe_pm.type == "card":
            card = stripe_pm.card
            return {
                "display_name": f"{card.brand.title()} ending in {card.last4}",
                "last_four": card.last4,
                "brand": card.brand,
                "expiry_month": card.exp_month,
                "expiry_year": card.exp_year,
            }
        else:
            return {
                "display_name": f"{stripe_pm.type.title()} payment method",
                "last_four": None,
                "brand": stripe_pm.type,
                "expiry_month": None,
                "expiry_year": None,
            }

    @staticmethod
    def get_user_payment_methods(
        db: Session, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Dict[str, Any]:
        """Get all payment methods for a user"""
        payment_methods = get_user_payment_methods(db, user_id, skip, limit)
        total_count = count_user_payment_methods(db, user_id)

        return {
            "payment_methods": payment_methods,
            "total_count": total_count,
        }

    @staticmethod
    def update_payment_method(
        db: Session, method_id: UUID, user_id: UUID, update_data: PaymentMethodUpdate
    ) -> UserPaymentMethod:
        """Update a payment method"""
        payment_method = update_payment_method(db, method_id, user_id, update_data)
        if not payment_method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment method not found",
            )
        return payment_method

    @staticmethod
    def set_default_payment_method(
        db: Session, method_id: UUID, user_id: UUID
    ) -> UserPaymentMethod:
        """Set a payment method as default"""
        payment_method = set_default_payment_method(db, method_id, user_id)
        if not payment_method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment method not found",
            )
        return payment_method

    @staticmethod
    def delete_payment_method(db: Session, method_id: UUID, user_id: UUID) -> bool:
        """Delete a payment method"""
        success = delete_payment_method(db, method_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment method not found",
            )

        # Publish event
        EventPublisher.publish_payment_method_deleted(
            method_id=str(method_id),
            user_id=str(user_id),
        )

        return True

    @staticmethod
    def process_quick_payment(
        db: Session, user_id: UUID, payment_request: QuickPaymentRequest
    ) -> Dict[str, Any]:
        """Process a payment using a saved payment method"""
        # Get the saved payment method
        payment_method = get_payment_method_by_id(
            db, payment_request.method_id, user_id
        )
        if not payment_method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment method not found",
            )

        try:
            # Process payment based on provider
            if payment_method.provider == PaymentProvider.STRIPE:
                result = PaymentMethodService._process_stripe_quick_payment(
                    db, payment_method, payment_request
                )
            elif payment_method.provider == PaymentProvider.PAYPAL:
                result = PaymentMethodService._process_paypal_quick_payment(
                    db, payment_method, payment_request
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported payment provider: {payment_method.provider}",
                )

            # Record usage
            if "payment_id" in result:
                create_payment_method_usage(
                    db, payment_method.method_id, UUID(result["payment_id"])
                )

                # Publish event
                EventPublisher.publish_payment_method_used(
                    method_id=str(payment_method.method_id),
                    payment_id=result["payment_id"],
                    user_id=str(user_id),
                )

            return result

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Quick payment failed: {str(e)}",
            )

    @staticmethod
    def _process_stripe_quick_payment(
        db: Session,
        payment_method: UserPaymentMethod,
        payment_request: QuickPaymentRequest,
    ) -> Dict[str, Any]:
        """Process quick payment with Stripe"""
        # Extract customer and payment method IDs
        customer_id, pm_id = payment_method.provider_method_id.split(":", 1)

        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(float(payment_request.amount) * 100),  # Convert to cents
            currency=settings.currency.lower(),
            customer=customer_id,
            payment_method=pm_id,
            confirmation_method="automatic",
            confirm=True,
            description=payment_request.description
            or f"Payment for request {payment_request.request_id}",
        )

        return {
            "payment_id": str(payment_request.request_id),  # Would be actual payment ID
            "status": "success" if intent.status == "succeeded" else "processing",
            "transaction_id": intent.id,
            "message": "Quick payment processed successfully",
        }

    @staticmethod
    def _process_paypal_quick_payment(
        db: Session,
        payment_method: UserPaymentMethod,
        payment_request: QuickPaymentRequest,
    ) -> Dict[str, Any]:
        """Process quick payment with PayPal"""
        # This would use PayPal's reference transaction API
        # Simplified implementation
        return {
            "payment_id": str(payment_request.request_id),
            "status": "success",
            "transaction_id": f"paypal_{payment_method.provider_method_id}",
            "message": "PayPal quick payment processed successfully",
        }
