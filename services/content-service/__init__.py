# Content Service Package
"""
Content Service - A microservice for content management and moderation.

This package provides:
- Content creation and management
- Content moderation and validation
- Media file handling
- Content categorization and tagging
"""

__version__ = "1.0.0"
__author__ = "Content Service Team"

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
