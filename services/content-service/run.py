#!/usr/bin/env python3
"""
Simple script to run the content service for development
"""
import uvicorn
import os

if __name__ == "__main__":
    # Set default environment variables for development
    os.environ.setdefault(
        "DATABASE_URL", "postgresql://devuser:devpass@localhost:5432/contentdb"
    )
    os.environ.setdefault("CONTENT_RETENTION_DAYS", "365")

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
