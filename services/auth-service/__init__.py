# Auth Service Package
"""
Auth Service - A microservice for user authentication and authorization.

This package provides:
- User authentication (login/logout)
- JWT token management
- Password hashing and verification
- Authorization middleware
"""

__version__ = "1.0.0"
__author__ = "Auth Service Team"

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
