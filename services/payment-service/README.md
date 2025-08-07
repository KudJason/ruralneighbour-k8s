# Payment Service

A microservice for handling payment processing, refunds, and payment history management in the RuralNeighbour platform.

## Features

- **Payment Processing**: Process payments through Stripe integration
- **Payment History**: Retrieve payment history with pagination
- **Refund Management**: Process refunds with admin approval
- **Event Publishing**: Publish payment lifecycle events to Redis streams
- **Event Consumption**: Consume service request events to create pending payments

## API Endpoints

### Payment Processing

- `POST /api/v1/payments/process` - Process a new payment (supports Stripe and PayPal)

### Payment History

- `GET /api/v1/payments/history` - Get payment history for a user

### Refund Management

- `POST /api/v1/payments/{payment_id}/refund` - Process a refund (admin only)

### PayPal-Specific Endpoints

- `POST /api/v1/payments/paypal/execute` - Execute PayPal payment after user approval
- `POST /api/v1/payments/paypal/cancel` - Cancel PayPal payment

## Database Schema

The service manages three main tables:

### Payments

- `payment_id` (UUID, Primary Key)
- `request_id` (UUID, Foreign Key to service requests)
- `payer_id` (UUID, User making the payment)
- `payee_id` (UUID, User receiving the payment)
- `amount` (DECIMAL(10,2))
- `payment_status` (ENUM: pending, processing, success, failed, cancelled)
- `payment_method` (ENUM: credit_card, debit_card, bank_transfer, digital_wallet)
- `transaction_id` (VARCHAR, External payment provider ID)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Payment History

- `history_id` (UUID, Primary Key)
- `payment_id` (UUID, Foreign Key to payments)
- `status` (ENUM)
- `notes` (TEXT)
- `created_at` (TIMESTAMP)

### Refunds

- `refund_id` (UUID, Primary Key)
- `payment_id` (UUID, Foreign Key to payments)
- `amount` (DECIMAL(10,2))
- `status` (ENUM: pending, approved, completed, rejected)
- `refund_reason` (TEXT)
- `approved_by` (UUID, Admin who approved)
- `created_at` (TIMESTAMP)
- `completed_at` (TIMESTAMP)

## Event System

### Published Events

| Event Name       | Stream            | Payload                                                                  |
| ---------------- | ----------------- | ------------------------------------------------------------------------ |
| PaymentProcessed | payment_lifecycle | `{payment_id, request_id, amount, status, timestamp}`                    |
| PaymentFailed    | payment_lifecycle | `{payment_id, request_id, amount, error_code, error_message, timestamp}` |
| PaymentRefunded  | payment_lifecycle | `{payment_id, request_id, amount, refund_reason, timestamp}`             |

### Consumed Events

| Event Name            | Stream            | Source                  | Action                        |
| --------------------- | ----------------- | ----------------------- | ----------------------------- |
| ServiceRequestCreated | service_lifecycle | Service Request Service | Create pending payment record |

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# PayPal
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
PAYPAL_MODE=sandbox

# Base URL for callbacks
BASE_URL=http://localhost:8000

# Security
SECRET_KEY=your-secret-key-change-in-production
```

## Running the Service

### Development

```bash
# Install common dependencies (from main pyproject.toml)
poetry install

# Install payment-specific dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/dbname"
export REDIS_URL="redis://localhost:6379/0"
export STRIPE_SECRET_KEY="sk_test_..."

# Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build the image
docker build -t payment-service .

# Run the container
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:password@localhost/dbname" \
  -e REDIS_URL="redis://localhost:6379/0" \
  -e STRIPE_SECRET_KEY="sk_test_..." \
  payment-service
```

**Note**: The Dockerfile installs both common dependencies (from pyproject.toml) and payment-specific dependencies (from requirements.txt).

## Testing

### Unit Tests

```bash
pytest tests/unit/
```

### Integration Tests

```bash
pytest tests/integration/
```

### API Tests

```bash
pytest tests/api/
```

## Security Considerations

- All payment endpoints should be secured with JWT authentication
- Sensitive payment data is handled according to PCI DSS guidelines
- Stripe handles card data securely
- Admin-only endpoints for refund processing
- Input validation and sanitization for all endpoints

## Dependencies

The payment service uses a hybrid dependency management approach:

### Common Dependencies (managed by main pyproject.toml)

- FastAPI - Web framework
- SQLAlchemy - ORM
- Redis - Event streaming
- PostgreSQL - Database
- Pydantic - Data validation
- Uvicorn - ASGI server

### Payment-Specific Dependencies

- Stripe - Payment processing
- PayPal SDK - PayPal payment processing

## Architecture

The service follows a clean architecture pattern:

```
app/
├── api/           # API endpoints
├── core/          # Configuration and utilities
├── crud/          # Database operations
├── db/            # Database setup
├── models/        # SQLAlchemy models
├── schemas/       # Pydantic models
└── services/      # Business logic
```

## Monitoring and Logging

- Payment processing events are logged
- Failed payments are tracked with error details
- Refund processing is logged with admin approval
- Event publishing/consumption is logged
- Database operations are logged for debugging

## Future Enhancements

- Webhook support for payment provider callbacks
- Multi-currency support
- Payment method management
- Subscription billing
- Payment analytics and reporting
- Fraud detection integration
