import json
from typing import Dict, Any, Optional
from datetime import datetime
import os

try:
    import redis
except ImportError:
    redis = None


class EventPublisher:
    """Event publisher using Redis Stream. Config from env, test可mock."""

    @staticmethod
    def get_redis_client():
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        if redis is None:
            raise RuntimeError("redis-py not installed")
        return redis.Redis.from_url(redis_url)

    @staticmethod
    def publish_event(stream: str, event_type: str, payload: dict) -> dict:
        """
        通用事件发布方法，自动生成 event_id、timestamp，标准化结构。
        """
        import uuid

        event = {
            "event_type": event_type,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
        }
        # payload 展开到 event
        for k, v in payload.items():
            if v is not None:
                event[k] = str(v)
        try:
            r = EventPublisher.get_redis_client()
            r.xadd(stream, {k: v for k, v in event.items()})
            print(f"[EVENT][PUBLISH] {event_type} -> {stream}: {json.dumps(event)}")
            return event
        except Exception as e:
            print(f"[EVENT][ERROR] Redis publish failed: {e}")
            return {"error": str(e), **event}

    @staticmethod
    def publish_payment_processed(
        payment_id: str, request_id: str, amount: str, status: str = "success"
    ):
        """
        发布支付成功事件到 payment_lifecycle 流
        """
        payload = {
            "payment_id": payment_id,
            "request_id": request_id,
            "amount": amount,
            "status": status,
        }
        return EventPublisher.publish_event(
            "payment_lifecycle", "PaymentProcessed", payload
        )

    @staticmethod
    def publish_payment_failed(
        payment_id: str,
        request_id: str,
        amount: str,
        error_code: str,
        error_message: str,
    ):
        """
        发布支付失败事件到 payment_lifecycle 流
        """
        payload = {
            "payment_id": payment_id,
            "request_id": request_id,
            "amount": amount,
            "error_code": error_code,
            "error_message": error_message,
        }
        return EventPublisher.publish_event(
            "payment_lifecycle", "PaymentFailed", payload
        )

    @staticmethod
    def publish_payment_refunded(
        payment_id: str, request_id: str, amount: str, refund_reason: str
    ):
        """
        发布退款事件到 payment_lifecycle 流
        """
        payload = {
            "payment_id": payment_id,
            "request_id": request_id,
            "amount": amount,
            "refund_reason": refund_reason,
        }
        return EventPublisher.publish_event(
            "payment_lifecycle", "PaymentRefunded", payload
        )

    @staticmethod
    def publish_payment_method_saved(method_id: str, user_id: str, method_type: str):
        """Publish payment method saved event"""
        payload = {
            "method_id": method_id,
            "user_id": user_id,
            "method_type": method_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return EventPublisher.publish_event(
            "payment_methods", "PaymentMethodSaved", payload
        )

    @staticmethod
    def publish_payment_method_deleted(method_id: str, user_id: str):
        """Publish payment method deleted event"""
        payload = {
            "method_id": method_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return EventPublisher.publish_event(
            "payment_methods", "PaymentMethodDeleted", payload
        )

    @staticmethod
    def publish_payment_method_used(method_id: str, payment_id: str, user_id: str):
        """Publish payment method used event"""
        payload = {
            "method_id": method_id,
            "payment_id": payment_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return EventPublisher.publish_event(
            "payment_methods", "PaymentMethodUsed", payload
        )

    @staticmethod
    def get_events(stream="payment_lifecycle", count=10):
        """从 Redis Stream 拉取事件（仅演示）"""
        try:
            r = EventPublisher.get_redis_client()
            msgs = r.xread({stream: "0"}, count=count, block=1000)
            return msgs if msgs is not None else []
        except Exception as e:
            print(f"[EVENT][ERROR] Redis get failed: {e}")
            return []


class EventConsumer:
    """Event consumer for payment service"""

    @staticmethod
    def consume_service_request_created(db, event_data):
        """
        消费 ServiceRequestCreated 事件，创建待处理支付记录
        """
        from ..services.payment_service import PaymentService
        from decimal import Decimal

        try:
            # Extract data from event
            request_id = event_data.get("request_id")
            payer_id = event_data.get("payer_id")
            payee_id = event_data.get("payee_id")
            amount = event_data.get("amount")

            if not all([request_id, payer_id, payee_id, amount]):
                print(
                    f"[EVENT][ERROR] Missing required fields in ServiceRequestCreated event: {event_data}"
                )
                return

            # Create pending payment
            payment = PaymentService.create_pending_payment(
                db=db,
                request_id=request_id,
                payer_id=payer_id,
                payee_id=payee_id,
                amount=Decimal(amount),
            )

            print(
                f"[EVENT][CONSUME] Created pending payment {payment.payment_id} for request {request_id}"
            )

        except Exception as e:
            print(f"[EVENT][ERROR] Failed to process ServiceRequestCreated event: {e}")

    @staticmethod
    def start_consumer(db):
        """
        启动事件消费者（示例实现）
        """
        try:
            r = EventConsumer.get_redis_client()
            # 这里可以实现持续监听逻辑
            # 简化实现，仅作演示
            pass
        except Exception as e:
            print(f"[EVENT][ERROR] Consumer failed: {e}")

    @staticmethod
    def get_redis_client():
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        if redis is None:
            raise RuntimeError("redis-py not installed")
        return redis.Redis.from_url(redis_url)
