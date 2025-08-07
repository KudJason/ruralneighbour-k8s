# Notification Service

A microservice for managing notifications and messages in the platform. This service handles all user-facing communications including real-time messaging, in-app notifications, push notifications, and emails.

## Features

- **Multi-channel Delivery**: Supports sending notifications via different channels (in-app, push, email)
- **Event-Driven**: Subscribes to events from all other business domains and translates them into user-facing notifications
- **Direct Messaging**: Provides endpoints for creating and retrieving direct messages between users
- **Notification Management**: Users can view their notifications and mark them as read
- **Real-time Messaging**: Support for real-time messaging between users
- **Notification Retention Policy**: Automatic cleanup of old notifications

## API Endpoints

### Messages

- `POST /api/v1/messages` - Create a new message
- `GET /api/v1/messages/{message_id}` - Get a specific message
- `GET /api/v1/messages/conversation/{user1_id}/{user2_id}` - Get conversation between two users
- `GET /api/v1/messages/user/{user_id}` - Get all messages for a user
- `GET /api/v1/messages/unread/{user_id}` - Get unread message count
- `PUT /api/v1/messages/{message_id}/read` - Mark a message as read
- `PUT /api/v1/messages/conversation/{user_id}/{other_user_id}/read` - Mark conversation as read
- `DELETE /api/v1/messages/{message_id}` - Delete a message

### Notifications

- `POST /api/v1/notifications` - Create a new notification
- `GET /api/v1/notifications/{notification_id}` - Get a specific notification
- `GET /api/v1/notifications/user/{user_id}` - Get notifications for a user
- `GET /api/v1/notifications/user/{user_id}/unread` - Get unread notifications
- `GET /api/v1/notifications/unread/{user_id}` - Get unread notification count
- `PUT /api/v1/notifications/{notification_id}/read` - Mark a notification as read
- `PUT /api/v1/notifications/user/{user_id}/read-all` - Mark all notifications as read
- `PUT /api/v1/notifications/{notification_id}/status` - Update delivery status
- `GET /api/v1/notifications/user/{user_id}/type/{notification_type}` - Get notifications by type
- `DELETE /api/v1/notifications/{notification_id}` - Delete a notification
- `DELETE /api/v1/notifications/cleanup` - Cleanup old notifications

### Events

- `POST /api/v1/events/user-registered` - Handle UserRegistered event
- `POST /api/v1/events/profile-updated` - Handle ProfileUpdated event
- `POST /api/v1/events/mode-changed` - Handle ModeChanged event
- `POST /api/v1/events/service-request-created` - Handle ServiceRequestCreated event
- `POST /api/v1/events/service-completed` - Handle ServiceCompleted event
- `POST /api/v1/events/payment-processed` - Handle PaymentProcessed event
- `POST /api/v1/events/payment-failed` - Handle PaymentFailed event
- `POST /api/v1/events/dispute-opened` - Handle DisputeOpened event
- `POST /api/v1/events/safety-report-filed` - Handle SafetyReportFiled event

## Database Schema

### Messages Table

```sql
CREATE TABLE messages (
    message_id UUID PRIMARY KEY,
    sender_id UUID NOT NULL REFERENCES users(user_id),
    recipient_id UUID NOT NULL REFERENCES users(user_id),
    service_request_id UUID,
    message_type VARCHAR(50) DEFAULT 'direct',
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Notifications Table

```sql
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id),
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    related_id UUID,
    delivery_method VARCHAR(50) NOT NULL,
    delivery_status VARCHAR(50) DEFAULT 'pending',
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `NOTIFICATION_RETENTION_DAYS`: Number of days to keep notifications (default: 90)
- `SENDGRID_API_KEY`: SendGrid API key for email notifications
- `FIREBASE_CREDENTIALS_PATH`: Path to Firebase credentials for push notifications
- `REDIS_URL`: Redis connection string for Celery
- `CELERY_BROKER_URL`: Celery broker URL
- `CELERY_RESULT_BACKEND`: Celery result backend URL

## Running the Service

### Development

```bash
python run.py
```

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t notification-service .
docker run -p 8000:8000 notification-service
```

## Testing

Run the tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app tests/
```

## Event Handling

This service is event-driven and handles the following events:

| Event Name            | Source                  | Action                         |
| --------------------- | ----------------------- | ------------------------------ |
| UserRegistered        | Auth Service            | Send welcome email             |
| ProfileUpdated        | User Service            | Notify user of profile changes |
| ModeChanged           | User Service            | Notify user of role change     |
| ServiceRequestCreated | Service Request Service | Notify nearby providers        |
| ServiceCompleted      | Service Request Service | Notify requester & provider    |
| PaymentProcessed      | Payment Service         | Send payment confirmation      |
| PaymentFailed         | Payment Service         | Alert user of payment failure  |
| DisputeOpened         | Safety Service          | Notify involved parties        |
| SafetyReportFiled     | Safety Service          | Alert admins                   |

## Architecture

- **FastAPI**: Web framework for building APIs
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization
- **PostgreSQL**: Primary database
- **Redis**: Message broker for Celery
- **Celery**: Background task processing
- **SendGrid**: Email delivery
- **Firebase**: Push notification delivery

## Security

- All endpoints require authentication via admin token
- Input validation using Pydantic schemas
- SQL injection protection via SQLAlchemy
- Rate limiting (to be implemented)

## Monitoring

- Health check endpoint: `GET /health`
- Service info endpoint: `GET /info`
- Structured logging for all operations
- Error tracking and alerting (to be implemented)

## Dependencies

- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL
- Redis
- Celery
- SendGrid
- Firebase Admin SDK
- pytest (testing)

## Files Created

- `requirements.txt` - Python dependencies
- `app/core/config.py` - Configuration settings
- `app/db/base.py` - Database configuration
- `app/db/init_db.py` - Database initialization
- `app/models/message.py` - Message model
- `app/models/notification.py` - Notification model
- `app/schemas/message.py` - Message Pydantic schemas
- `app/schemas/notification.py` - Notification Pydantic schemas
- `app/crud/message.py` - Message CRUD operations
- `app/crud/notification.py` - Notification CRUD operations
- `app/services/message_service.py` - Message business logic
- `app/services/notification_service.py` - Notification business logic
- `app/services/event_service.py` - Event handling logic
- `app/api/deps.py` - API dependencies
- `app/api/v1/endpoints/messages.py` - Message API endpoints
- `app/api/v1/endpoints/notifications.py` - Notification API endpoints
- `app/api/v1/endpoints/events.py` - Event API endpoints
- `app/main.py` - FastAPI application
- `Dockerfile` - Docker configuration
- `tests/conftest.py` - Test configuration
- `tests/test_message_service.py` - Message service tests
- `tests/test_notification_service.py` - Notification service tests
- `tests/test_event_service.py` - Event service tests
- `pytest.ini` - pytest configuration
- `run.py` - Development run script
- `README.md` - This documentation

## Status

**Complete and Ready for Development** ✅

The Notification Service has been fully implemented with:

- Complete CRUD operations for messages and notifications
- Event-driven notification system
- Multi-channel delivery support
- Comprehensive test coverage
- Docker containerization
- API documentation
- Database schema implementation
