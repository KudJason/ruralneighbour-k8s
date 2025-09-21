"""
消息队列测试配置和共享fixtures
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch


@pytest.fixture(scope="session")
def test_config():
    """测试配置"""
    return {
        "redis_url": "redis://localhost:6379/0",
        "test_database_url": "sqlite:///./test_message_queue.db",
        "max_events_per_test": 1000,
        "performance_threshold": {
            "min_events_per_second": 100,
            "max_latency_ms": 100,
            "max_memory_mb": 500
        }
    }


@pytest.fixture
def mock_redis_client():
    """模拟Redis客户端"""
    class MockRedisClient:
        def __init__(self):
            self.streams = {}
            self.connected = True
        
        def xadd(self, stream_name, data):
            if not self.connected:
                raise Exception("Redis connection failed")
            
            if stream_name not in self.streams:
                self.streams[stream_name] = []
            
            event_id = f"test-{len(self.streams[stream_name])}"
            self.streams[stream_name].append((event_id, data))
            return event_id
        
        def xread(self, streams, count=10, block=1000):
            result = []
            for stream_name, stream_id in streams.items():
                if stream_name in self.streams and self.streams[stream_name]:
                    result.append((stream_name, self.streams[stream_name]))
            return result
        
        def close(self):
            pass
    
    return MockRedisClient()


@pytest.fixture
def mock_database():
    """模拟数据库会话"""
    return Mock()


@pytest.fixture
def sample_event_data():
    """示例事件数据"""
    return {
        "service_request_created": {
            "event_type": "ServiceRequestCreated",
            "event_id": "test-event-id-1",
            "data": {
                "request_id": "test-request-id",
                "requester_id": "test-user-id",
                "service_type": "cleaning",
                "location": {"latitude": 40.7128, "longitude": -74.0060},
                "timestamp": "2023-01-01T00:00:00Z"
            }
        },
        "payment_processed": {
            "event_type": "PaymentProcessed",
            "event_id": "test-event-id-2",
            "data": {
                "payment_id": "test-payment-id",
                "request_id": "test-request-id",
                "amount": "50.00",
                "status": "success",
                "timestamp": "2023-01-01T00:00:00Z"
            }
        },
        "rating_created": {
            "event_type": "RatingCreated",
            "event_id": "test-event-id-3",
            "data": {
                "rating_id": "test-rating-id",
                "assignment_id": "test-assignment-id",
                "rater_id": "test-user-id",
                "ratee_id": "test-provider-id",
                "rating_score": 5,
                "timestamp": "2023-01-01T00:00:00Z"
            }
        }
    }


@pytest.fixture
def mock_notification_service():
    """模拟通知服务"""
    class MockNotificationService:
        def __init__(self):
            self.notifications = []
        
        def create_notification(self, user_id, title, message, notification_type):
            notification = {
                "id": f"notification-{len(self.notifications)}",
                "user_id": user_id,
                "title": title,
                "message": message,
                "type": notification_type,
                "created_at": "2023-01-01T00:00:00Z"
            }
            self.notifications.append(notification)
            return notification
        
        def get_notifications(self, user_id):
            return [n for n in self.notifications if n["user_id"] == user_id]
    
    return MockNotificationService()


@pytest.fixture
def mock_message_service():
    """模拟消息服务"""
    class MockMessageService:
        def __init__(self):
            self.messages = []
        
        def create_message(self, sender_id, recipient_id, message, conversation_id=None):
            msg = {
                "id": f"message-{len(self.messages)}",
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "message": message,
                "conversation_id": conversation_id,
                "created_at": "2023-01-01T00:00:00Z"
            }
            self.messages.append(msg)
            return msg
        
        def get_conversation(self, user1_id, user2_id):
            return [m for m in self.messages 
                   if (m["sender_id"] == user1_id and m["recipient_id"] == user2_id) or
                      (m["sender_id"] == user2_id and m["recipient_id"] == user1_id)]
    
    return MockMessageService()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """设置测试环境"""
    # 设置测试环境变量
    os.environ["TESTING"] = "true"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    
    # 添加服务路径到Python路径
    services_path = os.path.join(os.path.dirname(__file__), "../../")
    if services_path not in sys.path:
        sys.path.insert(0, services_path)
    
    yield
    
    # 清理测试环境
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


@pytest.fixture
def performance_monitor():
    """性能监控器"""
    import psutil
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.metrics = {}
        
        def start(self):
            self.start_time = time.time()
            self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        def stop(self):
            if self.start_time:
                self.metrics["duration"] = time.time() - self.start_time
            if self.start_memory:
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                self.metrics["memory_usage"] = current_memory - self.start_memory
        
        def get_metrics(self):
            return self.metrics
    
    return PerformanceMonitor()


# 测试标记
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "business: marks tests as business scenario tests"
    )




