# 消息队列测试套件

本测试套件专门为 RuralNeighbour 应用的消息队列系统设计，确保能够支持前端业务需求。

## 测试目标

1. **核心功能验证**：确保 EventPublisher 和 EventConsumer 正常工作
2. **业务场景覆盖**：验证完整的业务流程端到端功能
3. **性能要求**：确保系统能够支持高并发和低延迟需求
4. **可靠性保证**：验证系统在异常情况下的稳定性

## 测试结构

```
tests/
├── conftest.py                      # 测试配置和共享fixtures
├── test_message_queue_core.py       # 核心功能测试
├── test_business_scenarios.py       # 业务场景测试
├── test_message_queue_performance.py # 性能测试
├── run_message_queue_tests.py       # 测试运行脚本
└── README.md                        # 本文档
```

## 测试类型

### 1. 核心功能测试 (`test_message_queue_core.py`)

测试消息队列的基础功能：

- **EventPublisher 测试**

  - 服务请求创建事件发布
  - 支付处理事件发布
  - 评分创建事件发布
  - 事件数据序列化
  - Redis 连接错误处理

- **EventConsumer 测试**

  - 服务请求事件消费
  - 支付事件消费
  - 用户注册事件消费

- **可靠性测试**

  - 事件顺序性
  - 事件持久性
  - 高并发处理
  - 错误恢复

- **数据格式测试**
  - 事件结构标准化
  - 数据序列化正确性

### 2. 业务场景测试 (`test_business_scenarios.py`)

测试完整的业务流程：

- **服务请求生命周期**

  - 用户创建请求 → 服务商接受 → 服务完成 → 支付处理 → 评分
  - 包含支付的服务请求流程
  - 包含评分的服务请求流程

- **用户通信系统**

  - 用户间消息对话
  - 用户注册欢迎流程

- **支付流程**

  - 支付成功流程
  - 支付失败流程
  - 退款流程

- **实时通知功能**

  - 多种通知类型支持
  - 通知时序验证

- **系统可靠性**
  - 并发事件处理
  - 事件数据完整性

### 3. 性能测试 (`test_message_queue_performance.py`)

测试系统性能指标：

- **高并发性能**

  - 并发事件发布性能
  - 线程池性能

- **延迟性能**

  - 事件发布延迟
  - 批量事件延迟

- **内存性能**

  - 大量事件内存使用
  - 内存清理测试

- **系统稳定性**

  - 长时间运行稳定性
  - 错误恢复性能

- **可扩展性限制**
  - 最大并发流数量
  - 单流最大事件数量

## 运行测试

### 使用测试脚本

```bash
# 运行所有测试
python run_message_queue_tests.py --all

# 运行特定类型测试
python run_message_queue_tests.py --core
python run_message_queue_tests.py --business
python run_message_queue_tests.py --performance

# 详细输出
python run_message_queue_tests.py --all --verbose

# 生成覆盖率报告
python run_message_queue_tests.py --all --coverage
```

### 使用 pytest 直接运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_message_queue_core.py -v
pytest tests/test_business_scenarios.py -v
pytest tests/test_message_queue_performance.py -v

# 运行特定测试类
pytest tests/test_message_queue_core.py::TestEventPublisher -v

# 运行特定测试方法
pytest tests/test_message_queue_core.py::TestEventPublisher::test_publish_service_request_created -v

# 使用标记过滤
pytest tests/ -m "not slow" -v  # 跳过慢测试
pytest tests/ -m "performance" -v  # 只运行性能测试
```

## 测试数据

### 模拟 Redis Streams

测试使用`MockRedis`类模拟 Redis Streams 功能：

- 支持`xadd`、`xread`、`xgroup_create`、`xreadgroup`操作
- 线程安全的事件存储
- 模拟事件消费和通知创建
- 支持连接错误模拟

### 示例事件数据

测试包含标准的事件数据格式：

```json
{
	"event_type": "ServiceRequestCreated",
	"event_id": "uuid-string",
	"data": {
		"request_id": "uuid-string",
		"requester_id": "uuid-string",
		"service_type": "cleaning",
		"location": { "latitude": 40.7128, "longitude": -74.006 },
		"timestamp": "2023-01-01T00:00:00Z"
	}
}
```

## 性能指标

### 延迟要求

- 平均延迟：< 10ms
- 最大延迟：< 100ms
- 95%延迟：< 50ms
- 99%延迟：< 100ms

### 吞吐量要求

- 最小事件/秒：100
- 并发测试：1000 事件/秒
- 线程池测试：500 事件/秒

### 内存要求

- 内存增长：< 500MB
- 每事件内存：< 1KB
- 支持内存清理

## 前端业务需求支持

### 实时通知场景

测试覆盖以下前端业务场景：

1. **服务请求状态变化**

   - 用户创建请求 → 服务商接受 → 服务进行中 → 服务完成
   - 每个状态变化都触发相应的通知

2. **支付状态更新**

   - 支付成功/失败 → 退款处理
   - 实时通知用户支付状态

3. **消息通信**

   - 用户间实时消息
   - 对话状态维护

4. **评分系统**
   - 评分完成通知
   - 评分数据传递

### 用户体验要求

- **低延迟**：通知在几秒内到达
- **可靠性**：重要事件不丢失
- **顺序性**：状态变化按正确顺序处理
- **实时性**：支持实时更新

## 故障排除

### 常见问题

1. **导入错误**

   - 确保 Python 路径包含服务目录
   - 检查依赖包是否安装

2. **测试失败**

   - 检查 MockRedis 实现
   - 验证事件数据格式
   - 确认测试环境配置

3. **性能测试失败**
   - 检查系统资源
   - 调整性能阈值
   - 验证并发设置

### 调试技巧

1. **使用详细输出**

   ```bash
   pytest tests/ -v -s
   ```

2. **运行单个测试**

   ```bash
   pytest tests/test_message_queue_core.py::TestEventPublisher::test_publish_service_request_created -v -s
   ```

3. **使用 pdb 调试**
   ```bash
   pytest tests/ --pdb
   ```

## 扩展测试

### 添加新测试

1. **创建测试文件**

   ```python
   import pytest
   from conftest import mock_redis_client, sample_event_data

   class TestNewFeature:
       def test_new_functionality(self, mock_redis_client):
           # 测试实现
           pass
   ```

2. **添加性能测试**

   ```python
   @pytest.mark.performance
   def test_performance_feature(self, performance_monitor):
       performance_monitor.start()
       # 性能测试代码
       performance_monitor.stop()
       metrics = performance_monitor.get_metrics()
       assert metrics["duration"] < 1.0
   ```

3. **添加业务场景测试**
   ```python
   @pytest.mark.business
   def test_business_scenario(self, mock_redis_client, mock_notification_service):
       # 业务场景测试
       pass
   ```

## 持续集成

### GitHub Actions 配置

```yaml
name: Message Queue Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run core tests
        run: python run_message_queue_tests.py --core
      - name: Run business tests
        run: python run_message_queue_tests.py --business
      - name: Run performance tests
        run: python run_message_queue_tests.py --performance
```

## 总结

本测试套件提供了全面的消息队列测试覆盖，确保系统能够：

1. ✅ 支持前端实时业务需求
2. ✅ 处理高并发事件
3. ✅ 保证低延迟响应
4. ✅ 维护数据一致性
5. ✅ 提供可靠的错误处理

通过运行这些测试，可以确保消息队列系统能够满足 RuralNeighbour 应用的所有业务需求。




