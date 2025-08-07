from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationCreate,
    NotificationType,
    DeliveryMethod,
)
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EventService:
    """Service for handling events and creating notifications"""

    @staticmethod
    def handle_user_registered(
        db: Session, event_data: Dict[str, Any]
    ) -> Optional[str]:
        """Handle UserRegistered event - send welcome email"""
        try:
            user_id = event_data.get("user_id")
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
            user_id = event_data.get("user_id")

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
            user_id = event_data.get("user_id")
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
            requester_id = event_data.get("requester_id")
            request_id = event_data.get("request_id")
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
            requester_id = event_data.get("requester_id")
            provider_id = event_data.get("provider_id")
            request_id = event_data.get("request_id")

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
            payer_id = event_data.get("payer_id")
            payee_id = event_data.get("payee_id")
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
            user_id = event_data.get("user_id")
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
            user_id = event_data.get("user_id")
            dispute_id = event_data.get("dispute_id")

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
            reporter_id = event_data.get("reporter_id")
            report_id = event_data.get("report_id")

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
