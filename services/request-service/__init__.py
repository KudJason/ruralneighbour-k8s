# Request Service Package
"""
Request Service - A microservice for managing service requests and matching.

This package provides:
- Service request creation and management
- Request matching algorithms
- Request status tracking
- Request validation and processing
"""

__version__ = "1.0.0"
__author__ = "Request Service Team"

# Import main components for easy access
try:
    from app.main import app
    from app.core.config import settings
except ImportError:
    # Allow package to be imported even if dependencies are not available
    pass

__all__ = [
    "app",
    "settings",
]
