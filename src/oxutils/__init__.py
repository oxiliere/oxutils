"""OxUtils - Production-ready utilities for Django applications.

This package provides:
- JWT authentication with JWKS support
- Multi-tenant architecture (django-tenants integration, middleware, signals)
- Auth system: invitations, MFA, password reset, registration, sessions
- Structured logging with correlation IDs
- Audit system with S3 export
- Celery integration
- Django model mixins (ChangeTracker, CookieToken, SafeDelete)
- Permission management & authorization
- PDF generation
- Pagination utilities
- Currency utilities
- Custom exceptions, enums, and type definitions
"""

__version__ = "0.3.1"

from oxutils.conf import AUDIT_MIDDLEWARE, UTILS_APPS
from oxutils.settings import oxi_settings

__all__ = [
    "oxi_settings",
    "UTILS_APPS",
    "AUDIT_MIDDLEWARE",
    "__version__",
]
