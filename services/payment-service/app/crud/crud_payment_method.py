from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from uuid import UUID

from ..models.payment_method import UserPaymentMethod, PaymentMethodUsage
from ..schemas.payment_method import PaymentMethodCreate, PaymentMethodUpdate


def create_payment_method(
    db: Session, payment_method: PaymentMethodCreate, user_id: UUID
) -> UserPaymentMethod:
    """Create a new payment method for a user"""

    # If this should be the default, unset other defaults first
    if payment_method.set_as_default:
        db.query(UserPaymentMethod).filter(
            and_(
                UserPaymentMethod.user_id == user_id,
                UserPaymentMethod.is_default == True,
                UserPaymentMethod.is_active == True,
            )
        ).update({"is_default": False})

    db_payment_method = UserPaymentMethod(
        user_id=user_id,
        method_type=payment_method.method_type,
        provider=payment_method.provider,
        provider_method_id=payment_method.provider_token,  # This will be processed by service layer
        display_name=payment_method.display_name,
        is_default=payment_method.set_as_default,
    )

    db.add(db_payment_method)
    db.commit()
    db.refresh(db_payment_method)
    return db_payment_method


def get_payment_method_by_id(
    db: Session, method_id: UUID, user_id: UUID
) -> Optional[UserPaymentMethod]:
    """Get a payment method by ID for a specific user"""
    return (
        db.query(UserPaymentMethod)
        .filter(
            and_(
                UserPaymentMethod.method_id == method_id,
                UserPaymentMethod.user_id == user_id,
                UserPaymentMethod.is_active == True,
            )
        )
        .first()
    )


def get_user_payment_methods(
    db: Session, user_id: UUID, skip: int = 0, limit: int = 100
) -> List[UserPaymentMethod]:
    """Get all active payment methods for a user"""
    return (
        db.query(UserPaymentMethod)
        .filter(
            and_(
                UserPaymentMethod.user_id == user_id,
                UserPaymentMethod.is_active == True,
            )
        )
        .order_by(
            desc(UserPaymentMethod.is_default), desc(UserPaymentMethod.created_at)
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_default_payment_method(
    db: Session, user_id: UUID
) -> Optional[UserPaymentMethod]:
    """Get user's default payment method"""
    return (
        db.query(UserPaymentMethod)
        .filter(
            and_(
                UserPaymentMethod.user_id == user_id,
                UserPaymentMethod.is_default == True,
                UserPaymentMethod.is_active == True,
            )
        )
        .first()
    )


def update_payment_method(
    db: Session,
    method_id: UUID,
    user_id: UUID,
    payment_method_update: PaymentMethodUpdate,
) -> Optional[UserPaymentMethod]:
    """Update a payment method"""
    db_payment_method = get_payment_method_by_id(db, method_id, user_id)
    if not db_payment_method:
        return None

    update_data = payment_method_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_payment_method, field, value)

    db.commit()
    db.refresh(db_payment_method)
    return db_payment_method


def set_default_payment_method(
    db: Session, method_id: UUID, user_id: UUID
) -> Optional[UserPaymentMethod]:
    """Set a payment method as default"""
    # First, unset all other defaults for this user
    db.query(UserPaymentMethod).filter(
        and_(
            UserPaymentMethod.user_id == user_id,
            UserPaymentMethod.is_default == True,
            UserPaymentMethod.is_active == True,
        )
    ).update({"is_default": False})

    # Then set the specified method as default
    db_payment_method = get_payment_method_by_id(db, method_id, user_id)
    if not db_payment_method:
        return None

    db_payment_method.is_default = True
    db.commit()
    db.refresh(db_payment_method)
    return db_payment_method


def delete_payment_method(db: Session, method_id: UUID, user_id: UUID) -> bool:
    """Soft delete a payment method"""
    db_payment_method = get_payment_method_by_id(db, method_id, user_id)
    if not db_payment_method:
        return False

    # If this was the default, we need to handle that
    was_default = db_payment_method.is_default

    # Soft delete
    db_payment_method.is_active = False
    db_payment_method.is_default = False

    db.commit()

    # If this was the default, try to set another method as default
    if was_default:
        other_method = (
            db.query(UserPaymentMethod)
            .filter(
                and_(
                    UserPaymentMethod.user_id == user_id,
                    UserPaymentMethod.is_active == True,
                    UserPaymentMethod.method_id != method_id,
                )
            )
            .order_by(desc(UserPaymentMethod.created_at))
            .first()
        )
        if other_method:
            other_method.is_default = True
            db.commit()

    return True


def count_user_payment_methods(db: Session, user_id: UUID) -> int:
    """Count active payment methods for a user"""
    return (
        db.query(UserPaymentMethod)
        .filter(
            and_(
                UserPaymentMethod.user_id == user_id,
                UserPaymentMethod.is_active == True,
            )
        )
        .count()
    )


def create_payment_method_usage(
    db: Session, method_id: UUID, payment_id: UUID
) -> PaymentMethodUsage:
    """Record usage of a payment method"""
    usage = PaymentMethodUsage(
        method_id=method_id,
        payment_id=payment_id,
    )
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage


def get_payment_method_usage_history(
    db: Session, method_id: UUID, user_id: UUID, skip: int = 0, limit: int = 50
) -> List[PaymentMethodUsage]:
    """Get usage history for a payment method"""
    return (
        db.query(PaymentMethodUsage)
        .join(UserPaymentMethod)
        .filter(
            and_(
                PaymentMethodUsage.method_id == method_id,
                UserPaymentMethod.user_id == user_id,
            )
        )
        .order_by(desc(PaymentMethodUsage.used_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
