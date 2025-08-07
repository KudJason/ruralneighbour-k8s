# Location Service Testing

## Test Structure

The location service has two types of tests:

### 1. Unit Tests (Default)

- **Location**: `tests/test_location.py` and `test_structure.py`
- **Purpose**: Test individual functions and components without database dependencies
- **Database**: Uses mocked services and in-memory operations
- **PostGIS**: Not required

### 2. Integration Tests (Optional)

- **Location**: `tests/test_database_integration.py`
- **Purpose**: Test full database operations with PostGIS spatial functions
- **Database**: Requires PostgreSQL with PostGIS extension
- **PostGIS**: Required for spatial operations

## Running Tests

### Unit Tests (Default)

```bash
# From services directory
poe test-location

# Or directly
cd location-service && PYTHONPATH=. pytest
```

### Integration Tests (When PostGIS is available)

```bash
# From services directory
poe test-location-integration

# Or directly
cd location-service && PYTHONPATH=. pytest -m integration
```

### Skip Integration Tests

```bash
# Set environment variable to skip integration tests
SKIP_INTEGRATION_TESTS=true poe test-location
```

## Test Environment

The tests automatically detect the environment:

- **TESTING=true**: Uses SQLite for unit tests (PostGIS functions skipped)
- **SKIP_INTEGRATION_TESTS=true**: Skips integration tests
- **Default**: Runs unit tests only

## Database Models

The `UserAddress` model automatically adapts to the environment:

- **Production**: Uses PostGIS `Geography` column for spatial operations
- **Testing**: Uses `String` column for simple storage

## Integration Test Requirements

To run integration tests, you need:

1. PostgreSQL database
2. PostGIS extension installed
3. Proper database connection configured
4. Spatial functions available (`ST_GeomFromText`, etc.)

## Current Status

- ✅ Unit tests pass without PostGIS
- ✅ Integration tests are properly skipped when PostGIS unavailable
- ✅ PostGIS functionality preserved for production use
- ✅ Clean separation between unit and integration tests
