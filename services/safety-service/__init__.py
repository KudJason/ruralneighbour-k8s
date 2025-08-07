# Safety Service Package
"""
Safety Service - A microservice for safety monitoring and risk assessment.

This package provides:
- User safety verification
- Background checks
- Risk assessment algorithms
- Safety reporting and monitoring
"""

__version__ = "1.0.0"
__author__ = "Safety Service Team"

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
