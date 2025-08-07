# Notification Service Package
"""
Notification Service - A microservice for managing notifications and messaging.

This package provides:
- Push notifications
- Email notifications
- SMS notifications
- Notification preferences management
"""

__version__ = "1.0.0"
__author__ = "Notification Service Team"

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
