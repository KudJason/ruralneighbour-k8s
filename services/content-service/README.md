# Content Service

A microservice for managing and delivering non-transactional content such as news articles, videos, and system settings.

## Features

- **News Articles Management**: CRUD operations for news articles with admin-only creation/editing and public read access
- **Video Content Management**: CRUD operations for videos with type categorization and public delivery
- **System Settings**: Platform-wide configuration management
- **Content Retention Policy**: Automatic 1-year retention policy for content lifecycle management
- **Public Content Delivery**: Read-only endpoints for client applications
- **Admin-only Management**: Secure admin endpoints for content management

## API Endpoints

### Public Endpoints (No Authentication Required)

#### News Articles

- `GET /api/v1/news/articles` - Get all active news articles
- `GET /api/v1/news/articles/featured` - Get featured news articles
- `GET /api/v1/news/articles/{article_id}` - Get specific news article

#### Videos

- `GET /api/v1/videos` - Get all active videos
- `GET /api/v1/videos/featured` - Get featured videos
- `GET /api/v1/videos/type/{video_type}` - Get videos by type
- `GET /api/v1/videos/{video_id}` - Get specific video

### Admin Endpoints (Authentication Required)

#### News Articles

- `POST /api/v1/news/articles` - Create new news article
- `PUT /api/v1/news/articles/{article_id}` - Update news article
- `DELETE /api/v1/news/articles/{article_id}` - Delete news article

#### Videos

- `POST /api/v1/videos` - Create new video
- `PUT /api/v1/videos/{video_id}` - Update video
- `DELETE /api/v1/videos/{video_id}` - Delete video

#### System Settings

- `POST /api/v1/system/settings` - Create system setting
- `GET /api/v1/system/settings` - Get all system settings
- `GET /api/v1/system/settings/{setting_id}` - Get specific setting
- `GET /api/v1/system/settings/key/{setting_key}` - Get setting by key
- `PUT /api/v1/system/settings/{setting_id}` - Update setting
- `PUT /api/v1/system/settings/key/{setting_key}` - Update setting by key
- `DELETE /api/v1/system/settings/{setting_id}` - Delete setting

## Database Schema

### News Articles

```sql
CREATE TABLE news_articles (
    article_id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    author_id UUID REFERENCES users(user_id),
    image_url TEXT,
    is_featured BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    publish_date DATE,
    expiry_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Videos

```sql
CREATE TABLE videos (
    video_id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    video_url TEXT NOT NULL,
    thumbnail_url TEXT,
    video_type video_type,
    is_featured BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    publish_date DATE,
    expiry_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### System Settings

```sql
CREATE TABLE system_settings (
    setting_id UUID PRIMARY KEY,
    setting_key VARCHAR(255) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50),
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `CONTENT_RETENTION_DAYS`: Content retention period in days (default: 365)
- `SECRET_KEY`: JWT secret key for authentication
- `AUTH_SERVICE_URL`: Authentication service URL
- `USER_SERVICE_URL`: User service URL

## Running the Service

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://devuser:devpass@localhost:5432/contentdb"

# Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build the image
docker build -t content-service .

# Run the container
docker run -p 8000:8000 content-service
```

## Testing

Run unit tests:

```bash
pytest tests/
```

## Content Retention Policy

The service implements a 1-year retention policy for content:

- New content automatically gets an expiry date set to 1 year from creation
- Expired content is marked as inactive rather than deleted
- Retention statistics are available through the RetentionService
- Scheduled jobs can be implemented to handle retention policy enforcement

## Architecture

- **FastAPI**: Modern web framework for building APIs
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Primary database
- **Pydantic**: Data validation and serialization
- **Pytest**: Testing framework

## Service Dependencies

- PostgreSQL database
- Authentication service (for admin endpoints)
- User service (for author references)

## Security

- Admin endpoints require authentication
- Public endpoints are read-only
- Content retention policy ensures data lifecycle management
- Input validation through Pydantic schemas
