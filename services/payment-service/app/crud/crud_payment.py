from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID
from ..models.payment import (
    Payment,
    PaymentHistory,
    Refund,
    PaymentStatus,
    RefundStatus,
)
from ..schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
    PaymentHistoryCreate,
    RefundCreate,
    RefundUpdate,
)


def create_payment(db: Session, payment_in: PaymentCreate) -> Payment:
    payment = Payment(
        request_id=payment_in.request_id,
        payer_id=payment_in.payer_id,
        payee_id=payment_in.payee_id,
        amount=payment_in.amount,
        payment_method=payment_in.payment_method.value,
        payment_status=PaymentStatus.PENDING,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_payment_by_id(db: Session, payment_id: UUID) -> Optional[Payment]:
    return db.query(Payment).filter(Payment.payment_id == payment_id).first()


def get_payments_by_user(
    db: Session, user_id: UUID, skip: int = 0, limit: int = 100
) -> List[Payment]:
    return (
        db.query(Payment)
        .filter(Payment.payer_id == user_id)
        .order_by(desc(Payment.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_payments_by_request(db: Session, request_id: UUID) -> List[Payment]:
    return db.query(Payment).filter(Payment.request_id == request_id).all()


def update_payment(
    db: Session, payment_id: UUID, payment_update: PaymentUpdate
) -> Optional[Payment]:
    payment = get_payment_by_id(db, payment_id)
    if not payment:
        return None

    update_data = payment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)

    db.commit()
    db.refresh(payment)
    return payment


def create_payment_history(
    db: Session, history_in: PaymentHistoryCreate
) -> PaymentHistory:
    history = PaymentHistory(
        payment_id=history_in.payment_id,
        status=history_in.status.value,
        notes=history_in.notes,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_payment_history(db: Session, payment_id: UUID) -> List[PaymentHistory]:
    return (
        db.query(PaymentHistory)
        .filter(PaymentHistory.payment_id == payment_id)
        .order_by(desc(PaymentHistory.created_at))
        .all()
    )


def create_refund(db: Session, refund_in: RefundCreate) -> Refund:
    refund = Refund(
        payment_id=refund_in.payment_id,
        amount=refund_in.amount,
        refund_reason=refund_in.refund_reason,
        status=RefundStatus.PENDING,
    )
    db.add(refund)
    db.commit()
    db.refresh(refund)
    return refund


def get_refund_by_id(db: Session, refund_id: UUID) -> Optional[Refund]:
    return db.query(Refund).filter(Refund.refund_id == refund_id).first()


def update_refund(
    db: Session, refund_id: UUID, refund_update: RefundUpdate
) -> Optional[Refund]:
    refund = get_refund_by_id(db, refund_id)
    if not refund:
        return None

    update_data = refund_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(refund, field, value)

    db.commit()
    db.refresh(refund)
    return refund


def get_refunds_by_payment(db: Session, payment_id: UUID) -> List[Refund]:
    return db.query(Refund).filter(Refund.payment_id == payment_id).all()
