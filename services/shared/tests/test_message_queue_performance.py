"""
消息队列性能测试

测试目标：
1. 高并发事件处理性能
2. 事件处理延迟测试
3. 内存使用情况测试
4. 系统稳定性测试
"""

import pytest
import json
import uuid
import time
import threading
import psutil
import os
from datetime import datetime
from unittest.mock import Mock, patch
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed


class PerformanceMockRedis:
    """高性能模拟Redis Streams用于性能测试"""
    
    def __init__(self):
        self.streams = {}
        self.lock = threading.Lock()
        self.metrics = {
            "events_published": 0,
            "events_consumed": 0,
            "total_latency": 0.0,
            "max_latency": 0.0,
            "min_latency": float('inf')
        }
    
    def xadd(self, stream_name: str, data: Dict[str, Any]) -> str:
        """添加消息到流（线程安全）"""
        start_time = time.time()
        
        with self.lock:
            if stream_name not in self.streams:
                self.streams[stream_name] = []
            
            event_id = f"{int(time.time() * 1000)}-{len(self.streams[stream_name])}"
            self.streams[stream_name].append((event_id, data))
            
            # 更新指标
            self.metrics["events_published"] += 1
            
            # 计算延迟
            latency = time.time() - start_time
            self.metrics["total_latency"] += latency
            self.metrics["max_latency"] = max(self.metrics["max_latency"], latency)
            self.metrics["min_latency"] = min(self.metrics["min_latency"], latency)
            
            return event_id
    
    def xread(self, streams: Dict[str, str], count: int = 10, block: int = 1000) -> List:
        """读取流消息"""
        with self.lock:
            result = []
            for stream_name, stream_id in streams.items():
                if stream_name in self.streams:
                    messages = self.streams[stream_name]
                    if messages:
                        result.append((stream_name, messages))
                        self.metrics["events_consumed"] += len(messages)
            return result
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        with self.lock:
            avg_latency = (
                self.metrics["total_latency"] / self.metrics["events_published"]
                if self.metrics["events_published"] > 0 else 0
            )
            
            return {
                "events_published": self.metrics["events_published"],
                "events_consumed": self.metrics["events_consumed"],
                "average_latency": avg_latency,
                "max_latency": self.metrics["max_latency"],
                "min_latency": self.metrics["min_latency"] if self.metrics["min_latency"] != float('inf') else 0
            }


@pytest.fixture
def performance_redis():
    """提供高性能模拟Redis实例"""
    return PerformanceMockRedis()


class TestHighConcurrencyPerformance:
    """测试高并发性能"""
    
    def test_concurrent_event_publishing(self, performance_redis):
        """测试并发事件发布性能"""
        num_threads = 10
        events_per_thread = 100
        
        def publish_events(thread_id):
            """每个线程发布事件"""
            for i in range(events_per_thread):
                event_data = {
                    "event_type": "ConcurrentEvent",
                    "event_id": str(uuid.uuid4()),
                    "thread_id": thread_id,
                    "sequence": i,
                    "timestamp": datetime.utcnow().isoformat()
                }
                performance_redis.xadd("concurrent_stream", event_data)
        
        # 记录开始时间和内存使用
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        
        # 创建并启动线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=publish_events, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 记录结束时间和内存使用
        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        
        # 计算性能指标
        total_time = end_time - start_time
        total_events = num_threads * events_per_thread
        events_per_second = total_events / total_time
        memory_usage = end_memory - start_memory
        
        # 验证性能指标
        assert total_events == performance_redis.metrics["events_published"]
        assert events_per_second > 1000  # 至少1000事件/秒
        assert memory_usage < 100  # 内存使用不超过100MB
        
        print(f"并发性能测试结果:")
        print(f"  总事件数: {total_events}")
        print(f"  总时间: {total_time:.2f}秒")
        print(f"  事件/秒: {events_per_second:.2f}")
        print(f"  内存使用: {memory_usage:.2f}MB")
    
    def test_thread_pool_performance(self, performance_redis):
        """测试线程池性能"""
        num_workers = 20
        total_events = 1000
        
        def publish_event(event_id):
            """发布单个事件"""
            event_data = {
                "event_type": "ThreadPoolEvent",
                "event_id": str(uuid.uuid4()),
                "sequence": event_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            performance_redis.xadd("threadpool_stream", event_data)
            return event_id
        
        # 记录开始时间
        start_time = time.time()
        
        # 使用线程池执行
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(publish_event, i) for i in range(total_events)]
            
            # 等待所有任务完成
            completed = 0
            for future in as_completed(futures):
                future.result()
                completed += 1
        
        # 记录结束时间
        end_time = time.time()
        total_time = end_time - start_time
        events_per_second = total_events / total_time
        
        # 验证性能
        assert completed == total_events
        assert events_per_second > 500  # 至少500事件/秒
        
        print(f"线程池性能测试结果:")
        print(f"  工作线程数: {num_workers}")
        print(f"  总事件数: {total_events}")
        print(f"  总时间: {total_time:.2f}秒")
        print(f"  事件/秒: {events_per_second:.2f}")


class TestLatencyPerformance:
    """测试延迟性能"""
    
    def test_event_publishing_latency(self, performance_redis):
        """测试事件发布延迟"""
        num_events = 1000
        latencies = []
        
        for i in range(num_events):
            start_time = time.time()
            
            event_data = {
                "event_type": "LatencyTestEvent",
                "event_id": str(uuid.uuid4()),
                "sequence": i,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            performance_redis.xadd("latency_stream", event_data)
            
            latency = time.time() - start_time
            latencies.append(latency)
        
        # 计算延迟统计
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]
        
        # 验证延迟要求
        assert avg_latency < 0.01  # 平均延迟小于10ms
        assert max_latency < 0.1   # 最大延迟小于100ms
        assert p95_latency < 0.05  # 95%延迟小于50ms
        assert p99_latency < 0.1  # 99%延迟小于100ms
        
        print(f"延迟性能测试结果:")
        print(f"  平均延迟: {avg_latency*1000:.2f}ms")
        print(f"  最大延迟: {max_latency*1000:.2f}ms")
        print(f"  最小延迟: {min_latency*1000:.2f}ms")
        print(f"  95%延迟: {p95_latency*1000:.2f}ms")
        print(f"  99%延迟: {p99_latency*1000:.2f}ms")
    
    def test_batch_event_latency(self, performance_redis):
        """测试批量事件延迟"""
        batch_sizes = [1, 10, 50, 100]
        
        for batch_size in batch_sizes:
            start_time = time.time()
            
            # 批量发布事件
            for i in range(batch_size):
                event_data = {
                    "event_type": "BatchEvent",
                    "event_id": str(uuid.uuid4()),
                    "batch_size": batch_size,
                    "sequence": i,
                    "timestamp": datetime.utcnow().isoformat()
                }
                performance_redis.xadd("batch_stream", event_data)
            
            batch_time = time.time() - start_time
            events_per_second = batch_size / batch_time
            
            print(f"批量大小 {batch_size}: {events_per_second:.2f} 事件/秒")
            
            # 验证批量性能
            assert events_per_second > 100  # 至少100事件/秒


class TestMemoryPerformance:
    """测试内存性能"""
    
    def test_memory_usage_with_large_events(self, performance_redis):
        """测试大量事件的内存使用"""
        num_events = 10000
        large_data_size = 1024  # 1KB per event
        
        # 记录初始内存
        initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        
        # 发布大量事件
        for i in range(num_events):
            large_data = "x" * large_data_size
            event_data = {
                "event_type": "LargeDataEvent",
                "event_id": str(uuid.uuid4()),
                "sequence": i,
                "data": large_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            performance_redis.xadd("large_data_stream", event_data)
        
        # 记录最终内存
        final_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        # 验证内存使用
        assert memory_increase < 500  # 内存增长不超过500MB
        
        print(f"内存性能测试结果:")
        print(f"  事件数量: {num_events}")
        print(f"  每事件大小: {large_data_size} bytes")
        print(f"  内存增长: {memory_increase:.2f}MB")
        print(f"  每事件内存: {memory_increase * 1024 / num_events:.2f}KB")
    
    def test_memory_cleanup(self, performance_redis):
        """测试内存清理"""
        # 发布大量事件
        for i in range(1000):
            event_data = {
                "event_type": "CleanupTestEvent",
                "event_id": str(uuid.uuid4()),
                "sequence": i,
                "timestamp": datetime.utcnow().isoformat()
            }
            performance_redis.xadd("cleanup_stream", event_data)
        
        # 记录内存使用
        memory_before = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        
        # 清理事件（模拟）
        performance_redis.streams.clear()
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        # 记录清理后内存
        memory_after = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        memory_freed = memory_before - memory_after
        
        print(f"内存清理测试结果:")
        print(f"  清理前内存: {memory_before:.2f}MB")
        print(f"  清理后内存: {memory_after:.2f}MB")
        print(f"  释放内存: {memory_freed:.2f}MB")


class TestSystemStability:
    """测试系统稳定性"""
    
    def test_long_running_stability(self, performance_redis):
        """测试长时间运行稳定性"""
        duration = 10  # 10秒
        start_time = time.time()
        event_count = 0
        
        while time.time() - start_time < duration:
            event_data = {
                "event_type": "StabilityTestEvent",
                "event_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat()
            }
            performance_redis.xadd("stability_stream", event_data)
            event_count += 1
        
        # 验证稳定性
        assert event_count > 0
        events_per_second = event_count / duration
        
        print(f"稳定性测试结果:")
        print(f"  运行时间: {duration}秒")
        print(f"  总事件数: {event_count}")
        print(f"  平均事件/秒: {events_per_second:.2f}")
    
    def test_error_recovery_performance(self, performance_redis):
        """测试错误恢复性能"""
        # 正常发布事件
        for i in range(100):
            event_data = {
                "event_type": "NormalEvent",
                "event_id": str(uuid.uuid4()),
                "sequence": i,
                "timestamp": datetime.utcnow().isoformat()
            }
            performance_redis.xadd("recovery_stream", event_data)
        
        # 模拟错误（清空流）
        performance_redis.streams.clear()
        
        # 恢复并继续发布事件
        recovery_start = time.time()
        for i in range(100):
            event_data = {
                "event_type": "RecoveryEvent",
                "event_id": str(uuid.uuid4()),
                "sequence": i,
                "timestamp": datetime.utcnow().isoformat()
            }
            performance_redis.xadd("recovery_stream", event_data)
        
        recovery_time = time.time() - recovery_start
        
        # 验证恢复性能
        assert recovery_time < 1.0  # 恢复时间小于1秒
        
        print(f"错误恢复性能测试结果:")
        print(f"  恢复时间: {recovery_time:.2f}秒")
        print(f"  恢复后事件数: {len(performance_redis.streams['recovery_stream'])}")


class TestScalabilityLimits:
    """测试可扩展性限制"""
    
    def test_maximum_concurrent_streams(self, performance_redis):
        """测试最大并发流数量"""
        max_streams = 1000
        
        # 创建大量流
        for i in range(max_streams):
            stream_name = f"stream_{i}"
            event_data = {
                "event_type": "StreamTestEvent",
                "event_id": str(uuid.uuid4()),
                "stream_id": i,
                "timestamp": datetime.utcnow().isoformat()
            }
            performance_redis.xadd(stream_name, event_data)
        
        # 验证所有流都被创建
        assert len(performance_redis.streams) == max_streams
        
        print(f"最大并发流测试结果:")
        print(f"  创建流数量: {max_streams}")
        print(f"  实际流数量: {len(performance_redis.streams)}")
    
    def test_maximum_events_per_stream(self, performance_redis):
        """测试每个流的最大事件数量"""
        max_events = 10000
        stream_name = "max_events_stream"
        
        # 向单个流添加大量事件
        for i in range(max_events):
            event_data = {
                "event_type": "MaxEventTest",
                "event_id": str(uuid.uuid4()),
                "sequence": i,
                "timestamp": datetime.utcnow().isoformat()
            }
            performance_redis.xadd(stream_name, event_data)
        
        # 验证事件数量
        assert len(performance_redis.streams[stream_name]) == max_events
        
        print(f"单流最大事件测试结果:")
        print(f"  目标事件数: {max_events}")
        print(f"  实际事件数: {len(performance_redis.streams[stream_name])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




