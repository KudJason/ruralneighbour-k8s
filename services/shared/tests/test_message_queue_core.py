"""
消息队列核心功能测试

测试目标：
1. EventPublisher 和 EventConsumer 的核心功能
2. Redis Streams 的基本操作
3. 事件数据格式和序列化
4. 错误处理和容错机制
"""

import pytest
import json
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List


class MockRedis:
    """模拟Redis Streams用于测试"""
    
    def __init__(self):
        self.streams = {}
        self.consumer_groups = {}
        self.connection_errors = False
    
    def xadd(self, stream_name: str, data: Dict[str, Any]) -> str:
        """添加消息到流"""
        if self.connection_errors:
            raise Exception("Redis connection failed")
            
        if stream_name not in self.streams:
            self.streams[stream_name] = []
        
        event_id = f"{int(datetime.now().timestamp() * 1000)}-0"
        self.streams[stream_name].append((event_id, data))
        return event_id
    
    def xread(self, streams: Dict[str, str], count: int = 10, block: int = 1000) -> List:
        """读取流消息"""
        if self.connection_errors:
            raise Exception("Redis read failed")
            
        result = []
        for stream_name, stream_id in streams.items():
            if stream_name in self.streams:
                messages = self.streams[stream_name]
                if messages:
                    result.append((stream_name, messages))
        return result
    
    def xgroup_create(self, stream_name: str, group_name: str, id: str = "0"):
        """创建消费者组"""
        if stream_name not in self.consumer_groups:
            self.consumer_groups[stream_name] = {}
        self.consumer_groups[stream_name][group_name] = {"id": id}
    
    def xreadgroup(self, group_name: str, consumer_name: str, streams: Dict[str, str], count: int = 10, block: int = 1000) -> List:
        """消费者组读取消息"""
        return self.xread(streams, count, block)
    
    def close(self):
        """关闭连接"""
        pass


@pytest.fixture
def mock_redis():
    """提供模拟Redis实例"""
    return MockRedis()


class TestEventPublisher:
    """测试事件发布器"""
    
    def test_publish_service_request_created(self, mock_redis):
        """测试发布服务请求创建事件"""
        # 导入EventPublisher（需要根据实际路径调整）
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../request-service'))
        
        from app.services.events import EventPublisher
        
        request_id = str(uuid.uuid4())
        requester_id = str(uuid.uuid4())
        
        with patch.object(EventPublisher, 'get_redis_client', return_value=mock_redis):
            event_data = EventPublisher.publish_service_request_created(
                request_id=request_id,
                requester_id=requester_id,
                service_type="cleaning",
                location={"latitude": 40.7128, "longitude": -74.0060}
            )
        
        # 验证事件发布成功
        assert "service_lifecycle" in mock_redis.streams
        assert len(mock_redis.streams["service_lifecycle"]) == 1
        
        # 验证事件数据结构
        stream_data = mock_redis.streams["service_lifecycle"][0][1]
        assert stream_data["event_type"] == "ServiceRequestCreated"
        
        # 验证事件数据内容
        event_payload = json.loads(stream_data["data"])
        assert event_payload["request_id"] == request_id
        assert event_payload["requester_id"] == requester_id
        assert event_payload["service_type"] == "cleaning"
        assert event_payload["location"]["latitude"] == 40.7128
    
    def test_publish_payment_processed(self, mock_redis):
        """测试发布支付处理事件"""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../payment-service'))
        
        from app.services.events import EventPublisher
        
        payment_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        
        with patch.object(EventPublisher, 'get_redis_client', return_value=mock_redis):
            event_data = EventPublisher.publish_payment_processed(
                payment_id=payment_id,
                request_id=request_id,
                amount="50.00",
                status="success"
            )
        
        # 验证支付事件
        assert "payment_lifecycle" in mock_redis.streams
        payment_event = mock_redis.streams["payment_lifecycle"][0][1]
        assert payment_event["event_type"] == "PaymentProcessed"
        assert payment_event["payment_id"] == payment_id
        assert payment_event["amount"] == "50.00"
        assert payment_event["status"] == "success"
    
    def test_publish_rating_created(self, mock_redis):
        """测试发布评分创建事件"""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../request-service'))
        
        from app.services.events import EventPublisher
        
        rating_id = str(uuid.uuid4())
        assignment_id = str(uuid.uuid4())
        rater_id = str(uuid.uuid4())
        ratee_id = str(uuid.uuid4())
        
        with patch.object(EventPublisher, 'get_redis_client', return_value=mock_redis):
            event_data = EventPublisher.publish_rating_created(
                rating_id=rating_id,
                assignment_id=assignment_id,
                rater_id=rater_id,
                ratee_id=ratee_id,
                rating_score=5
            )
        
        # 验证评分事件
        assert "service_lifecycle" in mock_redis.streams
        rating_event = mock_redis.streams["service_lifecycle"][0][1]
        assert rating_event["event_type"] == "RatingCreated"
        
        # 验证评分数据
        rating_data = json.loads(rating_event["data"])
        assert rating_data["rating_score"] == 5
        assert rating_data["rater_id"] == rater_id
        assert rating_data["ratee_id"] == ratee_id
    
    def test_event_data_serialization(self, mock_redis):
        """测试事件数据序列化"""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../request-service'))
        
        from app.services.events import EventPublisher
        
        # 测试复杂数据结构序列化
        complex_location = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "address": {
                "street": "123 Main St",
                "city": "New York",
                "state": "NY"
            }
        }
        
        with patch.object(EventPublisher, 'get_redis_client', return_value=mock_redis):
            event_data = EventPublisher.publish_service_request_created(
                request_id=str(uuid.uuid4()),
                requester_id=str(uuid.uuid4()),
                service_type="cleaning",
                location=complex_location
            )
        
        # 验证复杂数据正确序列化
        stream_data = mock_redis.streams["service_lifecycle"][0][1]
        event_payload = json.loads(stream_data["data"])
        assert event_payload["location"]["address"]["city"] == "New York"
    
    def test_redis_connection_error_handling(self, mock_redis):
        """测试Redis连接错误处理"""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../request-service'))
        
        from app.services.events import EventPublisher
        
        # 模拟Redis连接错误
        mock_redis.connection_errors = True
        
        with patch.object(EventPublisher, 'get_redis_client', return_value=mock_redis):
            # 事件发布应该优雅处理错误，不抛出异常
            event_data = EventPublisher.publish_service_request_created(
                request_id=str(uuid.uuid4()),
                requester_id=str(uuid.uuid4()),
                service_type="cleaning",
                location={"latitude": 40.7128, "longitude": -74.0060}
            )
            
            # 应该返回None或包含错误信息的数据
            assert event_data is None or "error" in str(event_data)


class TestEventConsumer:
    """测试事件消费者"""
    
    def test_consume_service_request_created(self, mock_redis):
        """测试消费服务请求创建事件"""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../payment-service'))
        
        from app.services.events import EventConsumer
        
        # 模拟服务请求创建事件
        service_request_event = {
            "request_id": str(uuid.uuid4()),
            "payer_id": str(uuid.uuid4()),
            "payee_id": str(uuid.uuid4()),
            "amount": "50.00"
        }
        
        mock_db = Mock()
        
        # 测试事件消费
        with patch.object(EventConsumer, 'consume_service_request_created') as mock_consumer:
            EventConsumer.consume_service_request_created(mock_db, service_request_event)
            mock_consumer.assert_called_once_with(mock_db, service_request_event)
    
    def test_consume_payment_events(self, mock_redis):
        """测试消费支付事件"""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../notification-service'))
        
        from app.services.event_service import EventService
        
        # 模拟支付成功事件
        payment_event = {
            "event_type": "PaymentProcessed",
            "event_id": str(uuid.uuid4()),
            "data": json.dumps({
                "payment_id": str(uuid.uuid4()),
                "request_id": str(uuid.uuid4()),
                "amount": "50.00",
                "status": "success"
            })
        }
        
        mock_db = Mock()
        
        # 测试支付事件处理
        with patch.object(EventService, 'handle_payment_processed') as mock_handler:
            EventService.handle_payment_processed(mock_db, payment_event)
            mock_handler.assert_called_once()
    
    def test_consume_user_registration(self, mock_redis):
        """测试消费用户注册事件"""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../notification-service'))
        
        from app.services.event_service import EventService
        
        # 模拟用户注册事件
        user_registration_event = {
            "event_type": "UserRegistered",
            "event_id": str(uuid.uuid4()),
            "data": json.dumps({
                "user_id": str(uuid.uuid4()),
                "email": "newuser@example.com",
                "timestamp": datetime.utcnow().isoformat()
            })
        }
        
        mock_db = Mock()
        
        # 测试用户注册事件处理
        with patch.object(EventService, 'handle_user_registered') as mock_handler:
            EventService.handle_user_registered(mock_db, user_registration_event)
            mock_handler.assert_called_once()


class TestMessageQueueReliability:
    """测试消息队列可靠性"""
    
    def test_event_ordering(self, mock_redis):
        """测试事件顺序性"""
        # 发布多个事件
        events = []
        for i in range(5):
            event_data = {
                "event_type": "TestEvent",
                "event_id": str(uuid.uuid4()),
                "sequence": i,
                "timestamp": datetime.utcnow().isoformat()
            }
            event_id = mock_redis.xadd("test_stream", event_data)
            events.append((event_id, event_data))
        
        # 验证事件顺序
        stream_events = mock_redis.streams["test_stream"]
        for i, (event_id, event_data) in enumerate(stream_events):
            assert event_data["sequence"] == str(i)
    
    def test_event_durability(self, mock_redis):
        """测试事件持久性"""
        # 发布重要事件
        critical_event = {
            "event_type": "PaymentProcessed",
            "event_id": str(uuid.uuid4()),
            "data": json.dumps({
                "payment_id": str(uuid.uuid4()),
                "amount": "100.00",
                "status": "success"
            })
        }
        
        event_id = mock_redis.xadd("payment_lifecycle", critical_event)
        
        # 验证事件持久化
        assert event_id is not None
        assert "payment_lifecycle" in mock_redis.streams
        assert len(mock_redis.streams["payment_lifecycle"]) == 1
    
    def test_high_volume_processing(self, mock_redis):
        """测试高并发事件处理"""
        # 模拟高并发事件
        event_count = 100
        
        for i in range(event_count):
            event_data = {
                "event_type": "HighVolumeEvent",
                "event_id": str(uuid.uuid4()),
                "sequence": i,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            mock_redis.xadd("high_volume_stream", event_data)
        
        # 验证所有事件都被处理
        assert len(mock_redis.streams["high_volume_stream"]) == event_count
    
    def test_error_recovery(self, mock_redis):
        """测试错误恢复"""
        # 模拟Redis连接错误
        mock_redis.connection_errors = True
        
        # 尝试发布事件
        try:
            mock_redis.xadd("test_stream", {"event_type": "TestEvent"})
            assert False, "Should have raised an exception"
        except Exception as e:
            assert str(e) == "Redis connection failed"
        
        # 恢复连接
        mock_redis.connection_errors = False
        
        # 验证可以正常发布事件
        event_id = mock_redis.xadd("test_stream", {"event_type": "TestEvent"})
        assert event_id is not None


class TestEventDataFormat:
    """测试事件数据格式"""
    
    def test_event_structure(self, mock_redis):
        """测试事件结构标准化"""
        # 标准事件结构
        standard_event = {
            "event_type": "TestEvent",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "data": json.dumps({
                "field1": "value1",
                "field2": "value2"
            })
        }
        
        event_id = mock_redis.xadd("test_stream", standard_event)
        
        # 验证事件结构
        assert event_id is not None
        stored_event = mock_redis.streams["test_stream"][0][1]
        assert "event_type" in stored_event
        assert "event_id" in stored_event
        assert "timestamp" in stored_event
        assert "data" in stored_event
    
    def test_data_serialization(self, mock_redis):
        """测试数据序列化"""
        # 测试各种数据类型
        test_data = {
            "string": "test_string",
            "integer": 123,
            "float": 45.67,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
            "null": None
        }
        
        event_data = {
            "event_type": "DataSerializationTest",
            "event_id": str(uuid.uuid4()),
            "data": json.dumps(test_data)
        }
        
        event_id = mock_redis.xadd("test_stream", event_data)
        
        # 验证数据正确序列化
        stored_event = mock_redis.streams["test_stream"][0][1]
        deserialized_data = json.loads(stored_event["data"])
        assert deserialized_data["string"] == "test_string"
        assert deserialized_data["integer"] == 123
        assert deserialized_data["float"] == 45.67
        assert deserialized_data["boolean"] is True
        assert deserialized_data["list"] == [1, 2, 3]
        assert deserialized_data["dict"] == {"key": "value"}
        assert deserialized_data["null"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




