from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.schemas.payment_method import (
    PaymentMethodCreate,
    PaymentMethodUpdate,
    PaymentMethodOut,
    PaymentMethodListResponse,
    QuickPaymentRequest,
    SetDefaultPaymentMethodRequest,
)
from app.services.payment_method_service import PaymentMethodService
from app.db.session import get_db
from pydantic import BaseModel, Field

router = APIRouter()


def get_current_user_id() -> UUID:
    """Mock function to get current user ID from JWT token"""
    # In a real implementation, this would extract user ID from JWT token
    from uuid import uuid4

    return uuid4()


@router.post("/", response_model=PaymentMethodOut)
def save_payment_method(
    payment_method: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Save a new payment method for the current user
    """
    try:
        result = PaymentMethodService.save_payment_method(
            db, current_user_id, payment_method
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save payment method: {str(e)}",
        )


@router.get("/", response_model=PaymentMethodListResponse)
def list_payment_methods(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Get all saved payment methods for the current user
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


@router.put("/{method_id}", response_model=PaymentMethodOut)
def update_payment_method(
    method_id: UUID,
    payment_method_update: PaymentMethodUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Update a saved payment method
    """
    try:
        result = PaymentMethodService.update_payment_method(
            db, method_id, current_user_id, payment_method_update
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update payment method: {str(e)}",
        )


@router.put("/{method_id}/default", response_model=PaymentMethodOut)
def set_default_payment_method(
    method_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Set a payment method as the default
    """
    try:
        result = PaymentMethodService.set_default_payment_method(
            db, method_id, current_user_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set default payment method: {str(e)}",
        )


@router.delete("/{method_id}")
def delete_payment_method(
    method_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Delete a saved payment method
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


@router.post("/quick-payment")
def process_quick_payment(
    payment_request: QuickPaymentRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Process a payment using a saved payment method
    """
    try:
        result = PaymentMethodService.process_quick_payment(
            db, current_user_id, payment_request
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick payment failed: {str(e)}",
        )


# --- Compatibility alias endpoints for frontend ---


class MethodAliasCreateIn(BaseModel):
    type: str
    details: dict
    is_default: Optional[bool] = False


@router.post("/alias", response_model=PaymentMethodOut)
def alias_create_method(
    body: MethodAliasCreateIn,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Alias for POST /api/v1/payments/methods
    Maps frontend `{ type, details, is_default }` to internal schema.
    """
    try:
        # Map to internal create schema; we keep provider/method_type simple for now
        create_in = PaymentMethodCreate(
            method_type="card" if body.type in ("card", "stripe") else body.type,
            provider="stripe" if body.type in ("card", "stripe") else body.type,
            provider_token=body.details.get("payment_method_id") or body.details.get("token", ""),
            display_name=body.details.get("label") or body.details.get("brand"),
            set_as_default=bool(body.is_default),
        )
        result = PaymentMethodService.save_payment_method(db, current_user_id, create_in)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create method alias: {str(e)}",
        )


class MethodAliasUpdateIn(BaseModel):
    details: Optional[dict] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


@router.put("/{method_id}/alias", response_model=PaymentMethodOut)
def alias_update_method(
    method_id: UUID,
    body: MethodAliasUpdateIn,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Alias for PUT /api/v1/payments/methods/{id}
    Maps `{ details, is_default, is_active }` to our update + default endpoints.
    """
    try:
        updated = None
        if body.details is not None:
            display = body.details.get("label") or body.details.get("brand")
            updated = PaymentMethodService.update_payment_method(
                db, method_id, current_user_id, PaymentMethodUpdate(display_name=display)
            )
        if body.is_default is True:
            updated = PaymentMethodService.set_default_payment_method(
                db, method_id, current_user_id
            )
        if body.is_active is not None and updated is None:
            updated = PaymentMethodService.update_payment_method(
                db, method_id, current_user_id, PaymentMethodUpdate(is_active=body.is_active)
            )
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update method alias: {str(e)}",
        )
