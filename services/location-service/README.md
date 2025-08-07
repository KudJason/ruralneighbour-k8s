# Location Service

The Location Service manages addresses, validates locations against geographic business rules, and calculates distances using the Haversine formula.

## Features

- **Address Management**: Full CRUD operations for user addresses
- **Location Validation**: Enforces business rules (e.g., distance from restricted cities)
- **Distance Calculation**: Haversine distance calculation with multiple units
- **PostGIS Integration**: Spatial queries with geographic indexing
- **Performance Monitoring**: Ensures queries complete under 200ms

## API Endpoints

### Address Management (`/api/v1/addresses`)

- `POST /api/v1/addresses` - Create a new address
- `GET /api/v1/addresses` - List user's addresses
- `GET /api/v1/addresses/{address_id}` - Get specific address
- `PUT /api/v1/addresses/{address_id}` - Update address
- `DELETE /api/v1/addresses/{address_id}` - Delete address
- `GET /api/v1/addresses/primary` - Get user's primary address
- `GET /api/v1/addresses/search/radius` - Find addresses within radius

### Location Services (`/api/v1/locations`)

- `POST /api/v1/locations/validate` - Validate location against business rules
- `GET /api/v1/locations/distance` - Calculate distance between two points
- `GET /api/v1/locations/performance` - Check performance metrics

## Database Schema

### User Addresses

```sql
CREATE TABLE user_addresses (
    address_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    street_address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(100) NOT NULL DEFAULT 'USA',
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    is_within_service_area BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE,
    address_type VARCHAR(50) DEFAULT 'residential',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Spatial index for fast location-based queries
CREATE INDEX idx_user_addresses_location ON user_addresses USING GIST(location);
```

## Business Rules

### Location Validation

- **Rule**: Users cannot live within 2 miles of a city with population > 50,000
- **Implementation**: Validates coordinates against predefined restricted cities
- **Performance**: Must complete validation in under 200ms

### Distance Calculation

- **Method**: Haversine formula for accurate Earth surface distances
- **Units**: Supports miles, kilometers, and meters
- **Performance**: Must complete calculation in under 200ms

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string with PostGIS
- `RESTRICTED_CITY_POPULATION_THRESHOLD` - Population threshold for restricted cities (default: 50000)
- `RESTRICTED_AREA_RADIUS_MILES` - Radius around restricted cities (default: 2.0)
- `MAX_QUERY_TIME_MS` - Maximum allowed query time in milliseconds (default: 200)

## Running the Service

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL with PostGIS extension:

```sql
CREATE EXTENSION postgis;
```

3. Set environment variables:

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/locationdb"
```

4. Run the service:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Testing

### Integration Tests

Test the `/validate` endpoint with coordinates inside and outside restricted zones:

```bash
# Test valid location (far from restricted cities)
curl -X POST "http://localhost:8000/api/v1/locations/validate" \
  -H "Authorization: Bearer user-123e4567-e89b-12d3-a456-426614174000" \
  -H "Content-Type: application/json" \
  -d '{"latitude": 45.0, "longitude": -120.0}'

# Test invalid location (near New York)
curl -X POST "http://localhost:8000/api/v1/locations/validate" \
  -H "Authorization: Bearer user-123e4567-e89b-12d3-a456-426614174000" \
  -H "Content-Type: application/json" \
  -d '{"latitude": 40.8, "longitude": -74.0}'
```

### Performance Tests

Check if geospatial queries complete in under 200ms:

```bash
curl -X GET "http://localhost:8000/api/v1/locations/performance" \
  -H "Authorization: Bearer user-123e4567-e89b-12d3-a456-426614174000"
```

## Docker

Build and run with Docker:

```bash
docker build -t location-service .
docker run -p 8000:8000 location-service
```

## API Examples

### Create Address

```bash
curl -X POST "http://localhost:8000/api/v1/addresses" \
  -H "Authorization: Bearer user-123e4567-e89b-12d3-a456-426614174000" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "street_address": "123 Main St",
    "city": "Portland",
    "state": "OR",
    "postal_code": "97201",
    "latitude": 45.5152,
    "longitude": -122.6784,
    "is_primary": true
  }'
```

### Calculate Distance

```bash
curl -X GET "http://localhost:8000/api/v1/locations/distance?lat1=40.7128&lon1=-74.0060&lat2=34.0522&lon2=-118.2437&unit=miles" \
  -H "Authorization: Bearer user-123e4567-e89b-12d3-a456-426614174000"
```

## Performance Requirements

- **Geospatial queries** must complete in under 200ms
- **Location validation** must complete in under 200ms
- **Distance calculations** must complete in under 200ms
- **Spatial indexing** using PostGIS GIST indexes for optimal performance

## PostGIS Features

- **Geography type**: Uses PostGIS Geography for accurate Earth surface calculations
- **Spatial indexing**: GIST indexes for fast spatial queries
- **Distance functions**: ST_DWithin for radius searches
- **Coordinate system**: SRID 4326 (WGS84) for global compatibility
