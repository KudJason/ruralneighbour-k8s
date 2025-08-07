import redis
import asyncio
import json
import time
import threading
from typing import Dict, Any, List
from datetime import datetime
import logging
from app.core.config import REDIS_URL
from app.crud.crud_service_request import ServiceRequestCRUD
from app.models.service_request import PaymentStatus
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class EventConsumer:
    """
    Consumes events from Redis streams from other services.
    Based on the PRD requirements for event consumption.
    """

    def __init__(self):
        self.redis_url = REDIS_URL
        self.streams = {"payment_lifecycle": "0"}  # Start from beginning
        self.running = False

    def get_redis_client(self):
        """Get Redis client connection"""
        return redis.from_url(self.redis_url)

    def stop(self):
        """Stop consuming events"""
        self.running = False

    async def start_consuming(self):
        """Start consuming events from Redis streams"""
        self.running = True
        logger.info("Starting event consumer for request-service")

        while True:
            try:
                # 使用一个线程同步处理Redis读取，避免阻塞异步循环
                messages = []

                def read_redis_messages():
                    nonlocal messages
                    redis_client = self.get_redis_client()
                    try:
                        result = redis_client.xread(
                            {k: v for k, v in self.streams.items()},
                            count=10,
                            block=1000,
                        )
                        if result:
                            messages = result
                    except Exception as e:
                        logger.error(f"Error reading from Redis: {e}")
                    finally:
                        redis_client.close()

                # 创建线程并获取结果
                thread = threading.Thread(target=read_redis_messages)
                thread.start()
                thread.join(timeout=2)  # 等待最多2秒

                # 如果线程还活着，说明超时了，让它继续运行并跳过这一轮
                if thread.is_alive():
                    await asyncio.sleep(0.1)
                    continue

                if not messages:
                    await asyncio.sleep(0.1)
                    continue

                # 处理消息
                for stream_name, stream_messages in messages:
                    stream_name = (
                        stream_name.decode()
                        if isinstance(stream_name, bytes)
                        else stream_name
                    )

                    for message_id, fields in stream_messages:
                        try:
                            # Decode message
                            event_data = {}
                            for field, value in fields.items():
                                field_str = (
                                    field.decode()
                                    if isinstance(field, bytes)
                                    else field
                                )
                                value_str = (
                                    value.decode()
                                    if isinstance(value, bytes)
                                    else value
                                )

                                # Try to parse JSON values
                                try:
                                    event_data[field_str] = json.loads(value_str)
                                except (json.JSONDecodeError, TypeError):
                                    event_data[field_str] = value_str

                            # Process the event - 同步处理事件
                            def process_event_sync():
                                event_type = event_data.get("event_type", "")
                                if stream_name == "payment_lifecycle":
                                    if event_type == "PaymentProcessed":
                                        self.handle_payment_processed_sync(event_data)
                                    elif event_type == "PaymentFailed":
                                        self.handle_payment_failed_sync(event_data)
                                    else:
                                        logger.debug(
                                            f"Unhandled event type: {event_type} from {stream_name}"
                                        )
                                else:
                                    logger.debug(f"Unhandled stream: {stream_name}")

                            # 在新线程中处理事件
                            event_thread = threading.Thread(target=process_event_sync)
                            event_thread.start()
                            event_thread.join()

                            # Update stream position
                            self.streams[stream_name] = (
                                message_id.decode()
                                if isinstance(message_id, bytes)
                                else message_id
                            )

                        except Exception as e:
                            logger.error(
                                f"Error processing message from {stream_name}: {e}"
                            )
                            continue

            except Exception as e:
                logger.error(f"Error in event consumer: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    def handle_payment_processed_sync(self, event_data: Dict[str, Any]):
        """
        Handle PaymentProcessed event from Payment Service (synchronous version)
        Update the payment_status of a service_request to "paid"
        """
        request_id = event_data.get("request_id")
        if not request_id:
            logger.error("PaymentProcessed event missing request_id")
            return

        try:
            db = SessionLocal()
            try:
                # Update payment status to paid
                updated_request = ServiceRequestCRUD.update_payment_status(
                    db=db, request_id=request_id, payment_status=PaymentStatus.PAID
                )

                if updated_request:
                    logger.info(
                        f"Updated payment status to 'paid' for request {request_id}"
                    )
                else:
                    logger.warning(
                        f"Service request {request_id} not found for payment update"
                    )
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling PaymentProcessed event: {e}")

    def handle_payment_failed_sync(self, event_data: Dict[str, Any]):
        """
        Handle PaymentFailed event from Payment Service (synchronous version)
        Update the payment_status of a service_request to "payment_failed"
        """
        request_id = event_data.get("request_id")
        if not request_id:
            logger.error("PaymentFailed event missing request_id")
            return

        try:
            db = SessionLocal()
            try:
                # Update payment status to payment_failed
                updated_request = ServiceRequestCRUD.update_payment_status(
                    db=db,
                    request_id=request_id,
                    payment_status=PaymentStatus.PAYMENT_FAILED,
                )

                if updated_request:
                    logger.info(
                        f"Updated payment status to 'payment_failed' for request {request_id}"
                    )
                else:
                    logger.warning(
                        f"Service request {request_id} not found for payment update"
                    )
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling PaymentFailed event: {e}")

    def handle_user_status_changed(self, event_data: Dict[str, Any], db=None):
        """
        Handle UserStatusChanged event from User Service
        Process user status changes (suspend, delete, etc.)
        """
        user_id = event_data.get("user_id")
        new_status = event_data.get("new_status")

        if not user_id or not new_status:
            logger.error("UserStatusChanged event missing required fields")
            return

        try:
            # Use provided db connection for testing, otherwise create new one
            if db is None:
                db = SessionLocal()
                should_close = True
            else:
                should_close = False

            try:
                if new_status == "suspended":
                    # Cancel all active requests for this user
                    from app.models.service_request import ServiceRequestStatus

                    active_requests = ServiceRequestCRUD.get_user_requests(
                        db=db, requester_id=user_id, skip=0, limit=1000
                    )

                    for request in active_requests:
                        if request.status in [
                            ServiceRequestStatus.PENDING,
                            ServiceRequestStatus.ACCEPTED,
                        ]:
                            ServiceRequestCRUD.update_request_status(
                                db=db, request_id=request.request_id, status="cancelled"
                            )

                    logger.info(
                        f"Cancelled active requests for user {user_id} due to status: {new_status}"
                    )
                elif new_status == "deleted":
                    # Hard delete all requests for this user
                    from app.models.service_request import ServiceRequest

                    # Get all requests for the user
                    user_requests = (
                        db.query(ServiceRequest)
                        .filter(ServiceRequest.requester_id == user_id)
                        .all()
                    )

                    # Delete each request
                    for request in user_requests:
                        db.delete(request)

                    db.commit()
                    logger.info(
                        f"Hard deleted all requests for user {user_id} due to status: {new_status}"
                    )

            finally:
                if should_close:
                    db.close()

        except Exception as e:
            logger.error(f"Error handling UserStatusChanged event: {e}")

    def process_events(self, max_events: int = 10):
        """Process events from Redis streams (for testing)"""
        try:
            redis_client = self.get_redis_client()
            messages = redis_client.xread(
                {k: v for k, v in self.streams.items()},
                count=max_events,
                block=1000,
            )

            if messages:
                for stream_name, events in messages:
                    for event_id, event_data in events:
                        # Process the event
                        if b"event_type" in event_data:
                            event_type = event_data[b"event_type"].decode()
                            if event_type == "UserStatusChanged":
                                data = json.loads(event_data[b"data"].decode())
                                self.handle_user_status_changed(data)

            redis_client.close()
        except Exception as e:
            logger.error(f"Error processing events: {e}")


# Create global consumer instance
event_consumer = EventConsumer()
