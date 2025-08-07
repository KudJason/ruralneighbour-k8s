# Payment Service Tests

This directory contains tests for the Payment Service, including both unit tests and integration tests with real database operations.

## Test Structure

### Database Integration Tests

The service now includes proper database testing infrastructure:

- **`conftest.py`**: Contains pytest fixtures for database setup and teardown
- **`test_database_integration.py`**: Tests basic database operations (CRUD)
- **`test_payment_service_with_db.py`**: Tests service layer with real database

### Message/Event Tests

The service includes comprehensive event publishing and consuming tests:

- **`test_events.py`**: Tests EventPublisher and EventConsumer functionality
  - Tests all payment lifecycle events (processed, failed, refunded)
  - Tests payment method events (saved, deleted, used)
  - Tests Redis connection error handling
  - Tests event consumer functionality

### Traditional Mock Tests

- **`test_api.py`**: API endpoint tests using mocked dependencies
- **`test_payment_service.py`**: Service layer tests using mocked database
- **`test_payment_method_service.py`**: Payment method service tests
- **`test_paypal_service.py`**: PayPal integration tests

## Database Test Setup

### Test Database Configuration

The test database is configured in `conftest.py`:

```python
# Test database URL - using SQLite in-memory database for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_payment.db"
```

### Available Fixtures

- **`create_test_database`**: Creates all database tables at the beginning of test session
- **`clean_database`**: Cleans all data before each test for isolation
- **`db_session`**: Provides a test database session
- **`mock_get_db`**: Mocks the `get_db` dependency to return test session
- **`mock_redis`**: Mock Redis client for testing events
- **`override_redis`**: Overrides Redis client for all tests

### Usage Example

```python
def test_create_payment(db_session):
    """Test creating a payment in the database"""
    payment_data = PaymentCreate(
        request_id=uuid4(),
        payer_id=uuid4(),
        payee_id=uuid4(),
        amount=Decimal("100.00"),
        payment_method=PaymentMethod.CREDIT_CARD,
    )

    payment = create_payment(db_session, payment_data)
    assert payment.payment_id is not None
    assert payment.payment_status == PaymentStatus.PENDING
```

## Message/Event Testing

### Event Publisher Tests

Tests for publishing payment lifecycle events:

```python
def test_publish_payment_processed(mock_redis):
    """Test publishing PaymentProcessed event"""
    EventPublisher.publish_payment_processed(
        payment_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4()),
        amount="100.00",
        status="success"
    )

    # Verify event was published to Redis stream
    events = mock_redis.streams["payment_lifecycle"]
    assert len(events) == 1
    assert events[0][1]["event_type"] == "PaymentProcessed"
```

### Event Consumer Tests

Tests for consuming events and processing them:

```python
def test_consume_service_request_created(db_session, mock_redis):
    """Test consuming ServiceRequestCreated event"""
    event_data = {
        "request_id": str(uuid.uuid4()),
        "payer_id": str(uuid.uuid4()),
        "payee_id": str(uuid.uuid4()),
        "amount": "150.00",
    }

    # Mock the PaymentService.create_pending_payment method
    with patch("app.services.payment_service.PaymentService.create_pending_payment") as mock_create:
        EventConsumer.consume_service_request_created(db_session, event_data)
        mock_create.assert_called_once()
```

## Running Tests

### Run All Tests

```bash
python -m pytest tests/ -v
```

### Run Database Integration Tests Only

```bash
python -m pytest tests/test_database_integration.py -v
```

### Run Service Tests with Database

```bash
python -m pytest tests/test_payment_service_with_db.py -v
```

### Run Message/Event Tests

```bash
python -m pytest tests/test_events.py -v
```

### Run Traditional Mock Tests

```bash
python -m pytest tests/test_api.py tests/test_payment_service.py -v
```

## Test Database Features

### Automatic Setup and Teardown

- Database tables are created automatically before tests
- Data is cleaned between tests for isolation
- Tables are dropped after all tests complete

### Real Database Operations

- Tests use actual SQLAlchemy operations
- CRUD functions work with real database sessions
- Transaction rollback is properly tested

### Schema Validation

- Tests use proper Pydantic schemas (`PaymentCreate`, `PaymentMethodCreate`)
- Data validation is tested with real models
- Type safety is maintained throughout

## Message/Event Testing Features

### Mock Redis Implementation

- Uses a custom MockRedis class for testing
- Simulates Redis streams and operations
- Allows testing without real Redis instance

### Event Publishing Tests

- Tests all payment lifecycle events
- Tests payment method events
- Tests error handling for Redis connection issues
- Tests event data structure and content

### Event Consumer Tests

- Tests consuming ServiceRequestCreated events
- Tests handling missing or invalid event data
- Tests error handling for malformed events
- Tests consumer startup and shutdown

## Benefits of Database Testing

1. **Realistic Testing**: Tests actual database operations instead of mocks
2. **Schema Validation**: Ensures data models work correctly with database
3. **Transaction Testing**: Verifies proper transaction handling
4. **Integration Testing**: Tests the full stack from API to database
5. **Data Integrity**: Ensures foreign key relationships work correctly

## Benefits of Message Testing

1. **Event Reliability**: Ensures events are published correctly
2. **Data Consistency**: Verifies event data structure and content
3. **Error Handling**: Tests graceful handling of Redis failures
4. **Consumer Logic**: Tests event processing and business logic
5. **Integration**: Tests communication between services

## Migration from Mock Tests

To convert existing mock tests to use real database:

1. Replace `Mock()` database with `db_session` fixture
2. Use proper schema objects instead of dictionaries
3. Import and use actual CRUD functions
4. Update assertions to match real database behavior

Example:

```python
# Before (Mock)
mock_db = Mock()
mock_payment = Mock()
mock_payment.payment_id = uuid4()
mock_create_payment.return_value = mock_payment

# After (Real Database)
payment_data = PaymentCreate(...)
payment = create_payment(db_session, payment_data)
assert payment.payment_id is not None
```

## Notes

- Tests use SQLite for simplicity and speed
- In production, consider using PostgreSQL for more realistic testing
- Database files are created in the test directory and cleaned up automatically
- All tests are isolated and can run in parallel
- Message tests use MockRedis to avoid requiring a real Redis instance
- Event tests cover both publishing and consuming scenarios
