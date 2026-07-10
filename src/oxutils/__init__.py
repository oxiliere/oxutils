"""OxUtils — Production-ready Django utilities for multi-tenant SaaS.

Authentication & authorization:
    - JWT authentication: Bearer, Cookie, and passive backends with JWKS support
    - RBAC permissions: roles, groups, user grants with scope-based access
      control (``ScopePermission``, ``ScopeAnyPermission``, etc.)
    - Auto-discovery of permission presets from installed apps
    - Complete auth system: registration, login/logout, password reset,
      MFA, invitations, sessions — integrates with django-allauth
    - Api exceptions with error codes and structured responses

Multi-tenancy:
    - django-tenants integration with ``X-Organization-ID`` header routing
    - Tenant / tenant-user models, schema-aware middleware and caching
    - Tenant lifecycle signals, authorization, and system-tenant fallback

Infrastructure & tooling:
    - Structured logging with correlation IDs, request metadata binding,
      and pre-built ``LOGGING`` configuration (structlog)
    - Audit log export to S3 with export-state tracking and status history
    - Cursor-based pagination for Django Ninja APIs
    - PDF generation via WeasyPrint (``Printer`` class and ``WeasyTemplateView``)
    - Multi-currency support with rate syncing (BCC, Open Exchange Rates)
    - Celery app with task auto-discovery and structlog integration
    - S3 storage backend factory with env-var configuration

Model utilities:
    - Reusable mixins: UUID PK, timestamps, user tracking, slug, ordering,
      soft-delete with field masking (``SafeDeleteModelMixin``),
      change tracking, invoicing, and billing
    - Custom user model with email-based auth, ``oxi_id`` linking, and audit
    - Custom Pydantic types (``EmailApiType``, etc.)

Other:
    - HTTP header/cookie constants (oxi tokens, JWT tokens)
    - Template context processor (site name & domain)
    - Central pydantic-settings configuration (``oxi_settings``)
    - Shared enums (invoice status, export status)
    - Utility helpers: client IP detection, absolute URL building,
      image validation, bound-request detection
"""

__version__ = "0.4.6"

from oxutils.conf import AUDIT_MIDDLEWARE, UTILS_APPS
from oxutils.settings import oxi_settings

__all__ = [
    "oxi_settings",
    "UTILS_APPS",
    "AUDIT_MIDDLEWARE",
    "__version__",
]
