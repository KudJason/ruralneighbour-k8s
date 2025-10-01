#!/bin/bash
# Docker entrypoint script for microservices with Alembic migrations

set -e

echo "=================================================="
echo "Starting service with Alembic migrations..."
echo "=================================================="

# Wait for database to be ready
echo "Waiting for database..."
python << END
import time
import sys
from sqlalchemy import create_engine
import os

max_retries = 30
retry_interval = 2

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

for i in range(max_retries):
    try:
        engine = create_engine(database_url)
        connection = engine.connect()
        connection.close()
        print(f"✓ Database is ready!")
        break
    except Exception as e:
        if i == max_retries - 1:
            print(f"ERROR: Could not connect to database after {max_retries} attempts")
            print(f"Last error: {e}")
            sys.exit(1)
        print(f"Database not ready (attempt {i+1}/{max_retries}), waiting...")
        time.sleep(retry_interval)
END

# Run Alembic migrations or fallback to create_all
echo "Initializing database schema..."
if [ -f "alembic.ini" ] && [ -d "alembic/versions" ] && [ "$(ls -A alembic/versions/*.py 2>/dev/null | wc -l)" -gt 0 ]; then
    echo "Running Alembic migrations..."
    alembic upgrade head && echo "✓ Migrations completed successfully" || {
        echo "⚠️  Migration failed, falling back to SQLAlchemy create_all"
        python << 'PYEOF'
import os
import sys
try:
    from app.db.session import engine
    from app.db.base import Base
    # Import all models
    try:
        from app.models import *
    except:
        pass
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created via SQLAlchemy")
except Exception as e:
    print(f"ERROR: Could not initialize database: {e}")
    sys.exit(1)
PYEOF
    }
else
    echo "⚠️  No Alembic migrations found, using SQLAlchemy create_all"
    python << 'PYEOF'
import os
import sys
try:
    from app.db.session import engine
    from app.db.base import Base
    # Import all models
    try:
        from app.models import *
    except:
        pass
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created via SQLAlchemy")
except Exception as e:
    print(f"ERROR: Could not initialize database: {e}")
    sys.exit(1)
PYEOF
fi

echo "=================================================="
echo "Starting application..."
echo "=================================================="

# Execute the main command
exec "$@"
