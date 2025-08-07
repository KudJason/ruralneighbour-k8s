#!/usr/bin/env python3
"""
Run script for Notification Service
"""
import uvicorn
import os

if __name__ == "__main__":
    # Set default environment variables
    os.environ.setdefault(
        "DATABASE_URL", "postgresql://devuser:devpass@postgres:5432/notificationdb"
    )
    os.environ.setdefault("NOTIFICATION_RETENTION_DAYS", "90")

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
