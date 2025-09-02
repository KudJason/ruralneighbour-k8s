import logging
from typing import Any, Dict, Optional, cast

from app.core.config import settings
from app.schemas.notification import (
    DeliveryMethod,
    NotificationCreate,
    NotificationType,
)
from app.services.notification_service import NotificationService
from pydantic import UUID4
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EventService:
    """Service for handling events and creating notifications"""

    @staticmethod
    def handle_user_registered(
        db: Session, event_data: Dict[str, Any]
    ) -> Optional[str]:
        """Handle UserRegistered event - send welcome email"""
        try:
            user_id_raw = event_data.get("user_id")
            if not user_id_raw:
                raise ValueError("Missing user_id")
            user_id = cast(UUID4, user_id_raw)
            email = event_data.get("email")
            name = event_data.get("name", "User")

            notification_data = NotificationCreate(
                user_id=user_id,
                notification_type=NotificationType.WELCOME,
                title="Welcome to Our Platform!",
                content=f"Hi {name}, welcome to our platform! We're excited to have you on board.",
                delivery_method=DeliveryMethod.EMAIL,
            )

            notification = NotificationService.create_notification(
                db, notification_data
            )
            logger.info(f"Welcome notification created for user {user_id}")
            return str(notification.notification_id)

        except Exception as e:
            logger.error(f"Error handling UserRegistered event: {e}")
            return None

    @staticmethod
    def handle_profile_updated(
        db: Session, event_data: Dict[str, Any]
    ) -> Optional[str]:
        """Handle ProfileUpdated event - notify user of profile changes"""
        try:
            user_id_raw = event_data.get("user_id")
            if not user_id_raw:
                raise ValueError("Missing user_id")
            user_id = cast(UUID4, user_id_raw)

            notification_data = NotificationCreate(
                user_id=user_id,
                notification_type=NotificationType.PROFILE_UPDATE,
                title="Profile Updated",
                content="Your profile has been successfully updated.",
                delivery_method=DeliveryMethod.IN_APP,
            )

            notification = NotificationService.create_notification(
                db, notification_data
            )
            logger.info(f"Profile update notification created for user {user_id}")
            return str(notification.notification_id)

        except Exception as e:
            logger.error(f"Error handling ProfileUpdated event: {e}")
            return None

    @staticmethod
    def handle_mode_changed(db: Session, event_data: Dict[str, Any]) -> Optional[str]:
        """Handle ModeChanged event - notify user of role change"""
        try:
            user_id_raw = event_data.get("user_id")
            if not user_id_raw:
                raise ValueError("Missing user_id")
            user_id = cast(UUID4, user_id_raw)
            new_mode = event_data.get("new_mode", "NIN")

            notification_data = NotificationCreate(
                user_id=user_id,
                notification_type=NotificationType.MODE_CHANGE,
                title="Role Changed",
                content=f"Your role has been changed to {new_mode}.",
                delivery_method=DeliveryMethod.IN_APP,
            )

            notification = NotificationService.create_notification(
                db, notification_data
            )
            logger.info(f"Mode change notification created for user {user_id}")
            return str(notification.notification_id)

        except Exception as e:
            logger.error(f"Error handling ModeChanged event: {e}")
            return None

    @staticmethod
    def handle_service_request_created(
        db: Session, event_data: Dict[str, Any]
    ) -> Optional[str]:
        """Handle ServiceRequestCreated event - notify nearby providers"""
        try:
            requester_id_raw = event_data.get("requester_id")
            if not requester_id_raw:
                raise ValueError("Missing requester_id")
            requester_id = cast(UUID4, requester_id_raw)
            request_id = cast(Optional[UUID4], event_data.get("request_id"))
            service_type = event_data.get("service_type", "service")

            notification_data = NotificationCreate(
                user_id=requester_id,
                notification_type=NotificationType.SERVICE_REQUEST_CREATED,
                title="Service Request Created",
                content=f"Your {service_type} request has been created and is being sent to nearby providers.",
                related_id=request_id,
                delivery_method=DeliveryMethod.IN_APP,
            )

            notification = NotificationService.create_notification(
                db, notification_data
            )
            logger.info(f"Service request notification created for user {requester_id}")
            return str(notification.notification_id)

        except Exception as e:
            logger.error(f"Error handling ServiceRequestCreated event: {e}")
            return None

    @staticmethod
    def handle_service_completed(
        db: Session, event_data: Dict[str, Any]
    ) -> Optional[str]:
        """Handle ServiceCompleted event - notify requester and provider"""
        try:
            requester_id_raw = event_data.get("requester_id")
            provider_id_raw = event_data.get("provider_id")
            if not requester_id_raw or not provider_id_raw:
                raise ValueError("Missing requester_id or provider_id")
            requester_id = cast(UUID4, requester_id_raw)
            provider_id = cast(UUID4, provider_id_raw)
            request_id = cast(Optional[UUID4], event_data.get("request_id"))

            # Notify requester
            requester_notification = NotificationCreate(
                user_id=requester_id,
                notification_type=NotificationType.SERVICE_COMPLETED,
                title="Service Completed",
                content="Your service request has been completed. Please rate your experience.",
                related_id=request_id,
                delivery_method=DeliveryMethod.IN_APP,
            )

            # Notify provider
            provider_notification = NotificationCreate(
                user_id=provider_id,
                notification_type=NotificationType.SERVICE_COMPLETED,
                title="Service Completed",
                content="You have successfully completed a service request.",
                related_id=request_id,
                delivery_method=DeliveryMethod.IN_APP,
            )

            requester_notif = NotificationService.create_notification(
                db, requester_notification
            )
            provider_notif = NotificationService.create_notification(
                db, provider_notification
            )

            logger.info(
                f"Service completed notifications created for requester {requester_id} and provider {provider_id}"
            )
            return str(requester_notif.notification_id)

        except Exception as e:
            logger.error(f"Error handling ServiceCompleted event: {e}")
            return None

    @staticmethod
    def handle_payment_processed(
        db: Session, event_data: Dict[str, Any]
    ) -> Optional[str]:
        """Handle PaymentProcessed event - send payment confirmation"""
        try:
            payer_id_raw = event_data.get("payer_id")
            payee_id_raw = event_data.get("payee_id")
            if not payer_id_raw or not payee_id_raw:
                raise ValueError("Missing payer_id or payee_id")
            payer_id = cast(UUID4, payer_id_raw)
            payee_id = cast(UUID4, payee_id_raw)
            amount = event_data.get("amount", 0)

            # Notify payer
            payer_notification = NotificationCreate(
                user_id=payer_id,
                notification_type=NotificationType.PAYMENT_PROCESSED,
                title="Payment Processed",
                content=f"Your payment of ${amount} has been processed successfully.",
                delivery_method=DeliveryMethod.EMAIL,
            )

            # Notify payee
            payee_notification = NotificationCreate(
                user_id=payee_id,
                notification_type=NotificationType.PAYMENT_PROCESSED,
                title="Payment Received",
                content=f"You have received a payment of ${amount}.",
                delivery_method=DeliveryMethod.EMAIL,
            )

            payer_notif = NotificationService.create_notification(
                db, payer_notification
            )
            payee_notif = NotificationService.create_notification(
                db, payee_notification
            )

            logger.info(
                f"Payment processed notifications created for payer {payer_id} and payee {payee_id}"
            )
            return str(payer_notif.notification_id)

        except Exception as e:
            logger.error(f"Error handling PaymentProcessed event: {e}")
            return None

    @staticmethod
    def handle_payment_failed(db: Session, event_data: Dict[str, Any]) -> Optional[str]:
        """Handle PaymentFailed event - alert user of payment failure"""
        try:
            user_id_raw = event_data.get("user_id")
            if not user_id_raw:
                raise ValueError("Missing user_id")
            user_id = cast(UUID4, user_id_raw)
            amount = event_data.get("amount", 0)

            notification_data = NotificationCreate(
                user_id=user_id,
                notification_type=NotificationType.PAYMENT_FAILED,
                title="Payment Failed",
                content=f"Your payment of ${amount} has failed. Please check your payment method and try again.",
                delivery_method=DeliveryMethod.EMAIL,
            )

            notification = NotificationService.create_notification(
                db, notification_data
            )
            logger.info(f"Payment failed notification created for user {user_id}")
            return str(notification.notification_id)

        except Exception as e:
            logger.error(f"Error handling PaymentFailed event: {e}")
            return None

    @staticmethod
    def handle_dispute_opened(db: Session, event_data: Dict[str, Any]) -> Optional[str]:
        """Handle DisputeOpened event - notify involved parties and admins"""
        try:
            user_id_raw = event_data.get("user_id")
            if not user_id_raw:
                raise ValueError("Missing user_id")
            user_id = cast(UUID4, user_id_raw)
            dispute_id = cast(Optional[UUID4], event_data.get("dispute_id"))

            notification_data = NotificationCreate(
                user_id=user_id,
                notification_type=NotificationType.DISPUTE_OPENED,
                title="Dispute Opened",
                content="A dispute has been opened regarding your service. We will review and resolve this issue.",
                related_id=dispute_id,
                delivery_method=DeliveryMethod.IN_APP,
            )

            notification = NotificationService.create_notification(
                db, notification_data
            )
            logger.info(f"Dispute opened notification created for user {user_id}")
            return str(notification.notification_id)

        except Exception as e:
            logger.error(f"Error handling DisputeOpened event: {e}")
            return None

    @staticmethod
    def handle_safety_report_filed(
        db: Session, event_data: Dict[str, Any]
    ) -> Optional[str]:
        """Handle SafetyReportFiled event - alert admins of new safety report"""
        try:
            reporter_id_raw = event_data.get("reporter_id")
            if not reporter_id_raw:
                raise ValueError("Missing reporter_id")
            reporter_id = cast(UUID4, reporter_id_raw)
            report_id = cast(Optional[UUID4], event_data.get("report_id"))

            notification_data = NotificationCreate(
                user_id=reporter_id,
                notification_type=NotificationType.SAFETY_REPORT,
                title="Safety Report Filed",
                content="Your safety report has been filed and is being reviewed by our team.",
                related_id=report_id,
                delivery_method=DeliveryMethod.IN_APP,
            )

            notification = NotificationService.create_notification(
                db, notification_data
            )
            logger.info(f"Safety report notification created for user {reporter_id}")
            return str(notification.notification_id)

        except Exception as e:
            logger.error(f"Error handling SafetyReportFiled event: {e}")
            return None

    @staticmethod
    def handle_payment_refunded(
        db: Session, event_data: Dict[str, Any]
    ) -> Optional[str]:
        """Handle PaymentRefunded event - notify user of refund processing"""
        try:
            user_id_raw = event_data.get("user_id")
            if not user_id_raw:
                raise ValueError("Missing user_id")
            user_id = cast(UUID4, user_id_raw)
            amount = event_data.get("amount", 0)

            notification_data = NotificationCreate(
                user_id=user_id,
                notification_type=NotificationType.PAYMENT_REFUNDED,
                title="Payment Refunded",
                content=f"Your refund of ${amount} is being processed.",
                delivery_method=DeliveryMethod.EMAIL,
            )

            notification = NotificationService.create_notification(
                db, notification_data
            )
            logger.info(f"Payment refunded notification created for user {user_id}")
            return str(notification.notification_id)

        except Exception as e:
            logger.error(f"Error handling PaymentRefunded event: {e}")
            return None

    @staticmethod
    def handle_dispute_resolved(
        db: Session, event_data: Dict[str, Any]
    ) -> Optional[str]:
        """Handle DisputeResolved event - notify involved parties of resolution outcome"""
        try:
            user_id_raw = event_data.get("user_id")
            if not user_id_raw:
                raise ValueError("Missing user_id")
            user_id = cast(UUID4, user_id_raw)
            dispute_id = cast(Optional[UUID4], event_data.get("dispute_id"))
            outcome = event_data.get("outcome", "resolved")

            notification_data = NotificationCreate(
                user_id=user_id,
                notification_type=NotificationType.DISPUTE_RESOLVED,
                title="Dispute Resolved",
                content=f"Your dispute has been {outcome}.",
                related_id=dispute_id,
                delivery_method=DeliveryMethod.IN_APP,
            )

            notification = NotificationService.create_notification(
                db, notification_data
            )
            logger.info(f"Dispute resolved notification created for user {user_id}")
            return str(notification.notification_id)

        except Exception as e:
            logger.error(f"Error handling DisputeResolved event: {e}")
            return None

    @staticmethod
    def handle_rating_created(db: Session, event_data: Dict[str, Any]) -> Optional[str]:
        """Handle RatingCreated event - notify rated user of new rating"""
        try:
            rated_user_id_raw = event_data.get("rated_user_id")
            if not rated_user_id_raw:
                raise ValueError("Missing rated_user_id")
            rated_user_id = cast(UUID4, rated_user_id_raw)
            rating_value = event_data.get("rating_value")
            request_id = cast(Optional[UUID4], event_data.get("request_id"))

            content_text = (
                f"You received a new rating of {rating_value}."
                if rating_value is not None
                else "You received a new rating."
            )

            notification_data = NotificationCreate(
                user_id=rated_user_id,
                notification_type=NotificationType.RATING_CREATED,
                title="New Rating Received",
                content=content_text,
                related_id=request_id,
                delivery_method=DeliveryMethod.IN_APP,
            )

            notification = NotificationService.create_notification(
                db, notification_data
            )
            logger.info(f"Rating created notification for rated_user {rated_user_id}")
            return str(notification.notification_id)

        except Exception as e:
            logger.error(f"Error handling RatingCreated event: {e}")
            return None
