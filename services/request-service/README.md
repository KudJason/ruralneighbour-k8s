# Request Service

The Request Service is the core operational engine for managing service requests from creation to completion and rating.

## Features

- **Service Request Management**: Full CRUD operations for service requests
- **Provider Discovery**: Endpoints for LAH providers to find available requests
- **Assignment Management**: Handle service assignments and status updates
- **Event-Driven Architecture**: Publishes and consumes events for service lifecycle
- **Payment Integration**: Handles payment status updates from Payment Service

## API Endpoints

### Service Requests (`/api/v1/requests`)

- `POST /api/v1/requests` - Create a new service request
- `GET /api/v1/requests` - List user's service requests
- `GET /api/v1/requests/{request_id}` - Get specific service request
- `PUT /api/v1/requests/{request_id}` - Update service request
- `DELETE /api/v1/requests/{request_id}` - Delete service request

### Provider Endpoints (`/api/v1/providers`)

- `GET /api/v1/providers/available-requests` - Get available requests for providers
- `GET /api/v1/providers/assignments` - Get provider's assignments
- `GET /api/v1/providers/assignments/{assignment_id}` - Get specific assignment
- `GET /api/v1/providers/stats` - Get provider statistics

## Database Schema

### Service Requests

```sql
CREATE TABLE service_requests (
    request_id UUID PRIMARY KEY,
    requester_id UUID NOT NULL,
    title VARCHAR(255),
    description TEXT,
    service_type service_type_enum NOT NULL,
    pickup_latitude FLOAT NOT NULL,
    pickup_longitude FLOAT NOT NULL,
    destination_latitude FLOAT,
    destination_longitude FLOAT,
    offered_amount FLOAT,
    status service_request_status DEFAULT 'pending',
    payment_status payment_status DEFAULT 'unpaid',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Service Assignments

```sql
CREATE TABLE service_assignments (
    assignment_id UUID PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES service_requests(request_id),
    provider_id UUID NOT NULL,
    status assignment_status DEFAULT 'assigned',
    provider_notes TEXT,
    completion_notes TEXT,
    estimated_completion_time TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Ratings

```sql
CREATE TABLE ratings (
    rating_id UUID PRIMARY KEY,
    assignment_id UUID NOT NULL REFERENCES service_assignments(assignment_id),
    rater_id UUID NOT NULL,
    ratee_id UUID NOT NULL,
    rating_score INTEGER NOT NULL CHECK (rating_score >= 1 AND rating_score <= 5),
    review_text TEXT,
    is_provider_rating INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Event Publishing

The service publishes the following events to Redis streams:

### ServiceRequestCreated

- **Stream**: `service_lifecycle`
- **Payload**: `{ "request_id": "uuid", "requester_id": "uuid", "service_type": "string", "location": "geo-coordinates", "timestamp": "iso-8601" }`

### ServiceCompleted

- **Stream**: `service_lifecycle`
- **Payload**: `{ "request_id": "uuid", "assignment_id": "uuid", "requester_id": "uuid", "provider_id": "uuid", "completion_time": "iso-8601", "timestamp": "iso-8601" }`

### RatingCreated

- **Stream**: `service_lifecycle`
- **Payload**: `{ "rating_id": "uuid", "assignment_id": "uuid", "rater_id": "uuid", "ratee_id": "uuid", "rating_score": "int", "timestamp": "iso-8601" }`

## Event Consumption

The service consumes the following events:

### PaymentProcessed

- **Stream**: `payment_lifecycle`
- **Source**: Payment Service
- **Action**: Update payment_status to "paid"

### PaymentFailed

- **Stream**: `payment_lifecycle`
- **Source**: Payment Service
- **Action**: Update payment_status to "payment_failed"

## Environment Variables

- `DATABASE_URL` - Database connection string
- `REDIS_URL` - Redis connection string
- `MAX_REQUESTS_PER_USER` - Maximum active requests per user (default: 5)
- `SERVICE_RADIUS_MILES` - Service radius for location filtering (default: 2.0)
- `REQUEST_EXPIRY_HOURS` - Request expiry time in hours (default: 24)

## Running the Service

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set environment variables:

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/db"
export REDIS_URL="redis://localhost:6379/0"
```

3. Run the service:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Testing

Run tests with pytest:

```bash
pytest tests/
```

## Docker

Build and run with Docker:

```bash
docker build -t request-service .
docker run -p 8000:8000 request-service
```


