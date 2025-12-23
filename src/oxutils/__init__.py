"""OxUtils - Production-ready utilities for Django applications.

This package provides:
- JWT authentication with JWKS support
- S3 storage backends (static, media, private, logs)
- Structured logging with correlation IDs
- Audit system with S3 export
- Celery integration
- Django model mixins
- Custom exceptions
"""

__version__ = "0.1.7"

from oxutils.settings import oxi_settings
from oxutils.conf import UTILS_APPS, AUDIT_MIDDLEWARE

__all__ = [
    "oxi_settings",
    "UTILS_APPS",
    "AUDIT_MIDDLEWARE",
    "__version__",
]
