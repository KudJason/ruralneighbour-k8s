# Auth Service

A secure authentication microservice built with FastAPI that handles user registration, login, and token validation.

## Features

- ✅ User Registration with bcrypt password hashing
- ✅ User Login with JWT token generation
- ✅ Token validation (`/me` endpoint)
- ✅ Email uniqueness validation
- ✅ Event publishing (UserRegistered events)
- ✅ Comprehensive test suite
- ✅ Docker support

## API Endpoints

### POST /api/v1/auth/register

Register a new user account.

**Request:**

```json
{
	"email": "user@example.com",
	"password": "securepassword123",
	"full_name": "John Doe"
}
```

**Response:**

```json
{
	"user_id": "uuid",
	"email": "user@example.com",
	"full_name": "John Doe",
	"is_active": true,
	"is_verified": false,
	"created_at": "2024-01-01T00:00:00",
	"updated_at": "2024-01-01T00:00:00"
}
```

### POST /api/v1/auth/login

Authenticate user and get access token.

**Request:**

```json
{
	"email": "user@example.com",
	"password": "securepassword123"
}
```

**Response:**

```json
{
	"access_token": "jwt_token_here",
	"token_type": "bearer"
}
```

### GET /api/v1/auth/me

Validate token and get user information.

**Headers:**

```
Authorization: Bearer jwt_token_here
```

**Response:**

```json
{
	"sub": "user_id",
	"exp": 1640995200,
	"role": "user"
}
```

## Quick Start

### Option 1: Use Quick Start Script

```bash
python quick_start.py
```

### Option 2: Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python test_runner.py
# or
pytest tests/

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Docker

```bash
# Build image
docker build -t auth-service .

# Run container
docker run -p 8000:8000 auth-service
```

## Configuration

The service uses environment variables for configuration. Create a `.env` file:

```env
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-super-secret-jwt-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/test_auth.py::test_password_hash_and_verify -v

# Integration tests only
pytest tests/test_auth.py::test_register_success -v

# Security tests only
pytest tests/test_auth.py::test_password_is_hashed -v
```

## Database Schema

The service manages the `users` table:

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);
```

## Security Features

- Passwords are hashed with bcrypt
- JWT tokens have configurable expiration
- Email uniqueness is enforced
- SQL injection protection via SQLAlchemy ORM
- TODO: Rate limiting for brute-force protection

## Events

The service publishes events for integration with other microservices:

- `UserRegistered`: Published when a new user successfully registers

## Development

### Project Structure

```
auth-service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── auth.py       # API routes
│   ├── core/
│   │   ├── config.py            # Configuration
│   │   └── security.py          # JWT & password handling
│   ├── db/
│   │   ├── base.py              # SQLAlchemy base
│   │   └── session.py           # Database session
│   ├── models/
│   │   └── user.py              # User model
│   ├── schemas/
│   │   ├── user.py              # User Pydantic schemas
│   │   └── token.py             # Token schemas
│   ├── services/
│   │   ├── auth_service.py      # Business logic
│   │   └── events.py            # Event publishing
│   └── main.py                  # FastAPI app
├── tests/
│   └── test_auth.py             # Test suite
├── Dockerfile                   # Docker configuration
├── requirements.txt             # Python dependencies
├── quick_start.py              # Development server
└── test_runner.py              # Simple test runner
```

## TODO

- [ ] Implement rate limiting for login endpoint
- [ ] Add Redis/RabbitMQ for event publishing
- [ ] Add email verification flow
- [ ] Add password reset functionality
- [ ] Add user roles and permissions
- [ ] Add audit logging
- [ ] Add health check endpoint
