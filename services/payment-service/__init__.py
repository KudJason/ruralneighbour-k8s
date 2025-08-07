# Payment Service Package
"""
Payment Service - A microservice for payment processing and management.

This package provides:
- Payment processing (Stripe, PayPal)
- Payment method management
- Transaction history
- Payment validation and security
"""

__version__ = "1.0.0"
__author__ = "Payment Service Team"

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
