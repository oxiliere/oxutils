"""OxUtils - Production-ready utilities for Django applications.

This package provides:
- JWT authentication with JWKS support
- Structured logging with correlation IDs
- Audit system with S3 export
- Celery integration
- Django model mixins
- Custom exceptions
- Permission management
"""

__version__ = "0.2.1"

from oxutils.conf import AUDIT_MIDDLEWARE, UTILS_APPS
from oxutils.settings import oxi_settings

__all__ = [
    "oxi_settings",
    "UTILS_APPS",
    "AUDIT_MIDDLEWARE",
    "__version__",
]
