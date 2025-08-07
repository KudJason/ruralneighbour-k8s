# User Service Package
"""
User Service - A microservice for user profile and data management.

This package provides:
- User profile management (CRUD operations)
- User data validation
- Profile photo handling
- User preferences management
"""

__version__ = "1.0.0"
__author__ = "User Service Team"

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
