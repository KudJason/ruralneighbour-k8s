from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.api.deps import get_db_session, require_admin_auth
from app.services.event_service import EventService

router = APIRouter()


@router.post("/events/user-registered", tags=["events"])
async def handle_user_registered(
    event_data: Dict[str, Any],
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Handle UserRegistered event"""
    # Verify authentication
    require_admin_auth(authorization)

    notification_id = EventService.handle_user_registered(db, event_data)
    if notification_id:
        return {"notification_id": notification_id, "status": "created"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create welcome notification",
        )


@router.post("/events/profile-updated", tags=["events"])
async def handle_profile_updated(
    event_data: Dict[str, Any],
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Handle ProfileUpdated event"""
    # Verify authentication
    require_admin_auth(authorization)

    notification_id = EventService.handle_profile_updated(db, event_data)
    if notification_id:
        return {"notification_id": notification_id, "status": "created"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create profile update notification",
        )


@router.post("/events/mode-changed", tags=["events"])
async def handle_mode_changed(
    event_data: Dict[str, Any],
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Handle ModeChanged event"""
    # Verify authentication
    require_admin_auth(authorization)

    notification_id = EventService.handle_mode_changed(db, event_data)
    if notification_id:
        return {"notification_id": notification_id, "status": "created"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create mode change notification",
        )


@router.post("/events/service-request-created", tags=["events"])
async def handle_service_request_created(
    event_data: Dict[str, Any],
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Handle ServiceRequestCreated event"""
    # Verify authentication
    require_admin_auth(authorization)

    notification_id = EventService.handle_service_request_created(db, event_data)
    if notification_id:
        return {"notification_id": notification_id, "status": "created"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create service request notification",
        )


@router.post("/events/service-completed", tags=["events"])
async def handle_service_completed(
    event_data: Dict[str, Any],
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Handle ServiceCompleted event"""
    # Verify authentication
    require_admin_auth(authorization)

    notification_id = EventService.handle_service_completed(db, event_data)
    if notification_id:
        return {"notification_id": notification_id, "status": "created"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create service completion notification",
        )


@router.post("/events/payment-processed", tags=["events"])
async def handle_payment_processed(
    event_data: Dict[str, Any],
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Handle PaymentProcessed event"""
    # Verify authentication
    require_admin_auth(authorization)

    notification_id = EventService.handle_payment_processed(db, event_data)
    if notification_id:
        return {"notification_id": notification_id, "status": "created"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment processed notification",
        )


@router.post("/events/payment-failed", tags=["events"])
async def handle_payment_failed(
    event_data: Dict[str, Any],
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Handle PaymentFailed event"""
    # Verify authentication
    require_admin_auth(authorization)

    notification_id = EventService.handle_payment_failed(db, event_data)
    if notification_id:
        return {"notification_id": notification_id, "status": "created"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment failed notification",
        )


@router.post("/events/dispute-opened", tags=["events"])
async def handle_dispute_opened(
    event_data: Dict[str, Any],
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Handle DisputeOpened event"""
    # Verify authentication
    require_admin_auth(authorization)

    notification_id = EventService.handle_dispute_opened(db, event_data)
    if notification_id:
        return {"notification_id": notification_id, "status": "created"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create dispute opened notification",
        )


@router.post("/events/safety-report-filed", tags=["events"])
async def handle_safety_report_filed(
    event_data: Dict[str, Any],
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Handle SafetyReportFiled event"""
    # Verify authentication
    require_admin_auth(authorization)

    notification_id = EventService.handle_safety_report_filed(db, event_data)
    if notification_id:
        return {"notification_id": notification_id, "status": "created"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create safety report notification",
        )
