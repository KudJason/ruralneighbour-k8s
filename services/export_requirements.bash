#!/bin/bash
# Export requirements.txt for all services based on pyproject.toml

echo "🚀 Starting batch export of requirements.txt for all services..."

# Base dependencies that all services need
BASE_DEPS="fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
pydantic-settings==2.1.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
redis==5.0.1
alembic==1.13.1
passlib[bcrypt]==1.7.4
httpx==0.25.2
email-validator==2.0.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
pytest==7.4.3
pytest-asyncio==0.21.1"

# Function to create requirements for a service
create_requirements() {
    local service_name=$1
    local specific_deps=$2
    
    echo "📦 Exporting requirements for: $service_name"
    
    # Create the requirements.txt file
    cat > "$service_name/requirements.txt" << EOF
# $service_name Dependencies
$BASE_DEPS

# $service_name Specific Dependencies
$specific_deps
EOF
    
    echo "✅ Exported: $service_name/requirements.txt"
}

# Create requirements for each service
create_requirements "auth-service" "python-jose==3.3.0
requests==2.31.0"

create_requirements "user-service" "python-multipart==0.0.6"

create_requirements "location-service" "numpy<2.0.0
geoalchemy2==0.14.2
shapely==2.0.2"

create_requirements "payment-service" "stripe==8.10.0
paypalrestsdk==1.13.1"

create_requirements "request-service" ""

create_requirements "notification-service" ""

create_requirements "content-service" ""

create_requirements "safety-service" ""

echo "🎉 Batch export completed successfully!"