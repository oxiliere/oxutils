# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.10] - 2024-12-30

### Added
- **Permissions System**: Complete RBAC (Role-Based Access Control) implementation
  - `Role`, `Group`, `UserGroup` models for role management
  - `RoleGrant` for role-based permission templates
  - `Grant` model for user-specific permissions with context support
  - Action expansion system for permission wildcards
  - PostgreSQL GIN indexes for efficient permission queries
  - Group-specific role grants for fine-grained control
- **Oxiliere Multi-Tenant Enhancements**:
  - `BaseTenant` and `BaseTenantUser` abstract models
  - Soft delete support with `delete_tenant()` and `restore()` methods
  - Tenant status management with `TenantStatus` enum
  - User management with `add_user()` and `remove_user()` methods
  - Tenant signals: `tenant_user_added`, `tenant_user_removed`
  - Schema name generation utilities
  - System tenant protection
  - Authorization middleware and checks
- **JWT Enhancements**:
  - Extended JWT authentication with permission support
  - Token user model for JWT-based user representation
  - Improved JWT models and schemas
- **Model Improvements**:
  - New field types in `oxutils.models.fields`
  - Enhanced base model mixins
  - Better timestamp and tracking support
- **User Management**:
  - Enhanced user models with tenant integration
  - User permission management

### Changed
- **Test Suite Reorganization**: Tests restructured by module with isolated settings
  - `tests/common/` for common tests
  - `tests/oxiliere/` for multi-tenant tests
  - `tests/permissions/` for permission tests
  - Each module has its own `settings.py` for isolation
  - Improved test documentation in `tests/README.md`
- **Middleware**: Enhanced tenant middleware with better error handling
- **Permissions**: Improved permission controllers and schemas
- **Dependencies**: Updated dependency versions in `pyproject.toml`

### Fixed
- Permission grant override now preserves actions in expanded form
- Improved error handling in tenant operations

### Migration Guide
If upgrading from 0.1.9:
- Review new permission models and run migrations
- Update tenant models to inherit from `BaseTenant` and `BaseTenantUser`
- Update test imports if using test utilities

## [0.1.3] - 2024-12-08

### Added
- Context processor for site name and domain (`oxutils.context.site_name_processor`)
  - Provides `site_name` and `site_domain` from settings to templates
  - Easy integration with Django templates

## [0.1.0] - 2024-12-02

### Added

#### Core Features
- JWT authentication with RS256 and JWKS support
- Four S3 storage backends (Static, PublicMedia, PrivateMedia, LogStorage)
- Structured logging with `structlog` and correlation IDs
- Audit system with automatic change tracking and S3 export
- Celery integration with structured logging
- Pydantic-based settings management

#### Django Mixins
- `UUIDPrimaryKeyMixin` - UUID primary keys
- `TimestampMixin` - Automatic created_at/updated_at
- `BaseModelMixin` - Combined UUID + timestamps + is_active
- `NameMixin` - Name and description fields
- `UserTrackingMixin` - created_by/updated_by tracking
- `BaseService` - Service layer with exception handling

#### Exceptions
- `APIException` base class with standardized format
- `NotFoundException` (404)
- `ValidationException` (400)
- `ConflictException` (409)
- `DuplicateEntryException` (409)
- `PermissionDeniedException` (403)
- `UnauthorizedException` (401)
- `InvalidParameterException` (400)
- `MissingParameterException` (400)
- `InternalErrorException` (500)

#### Utilities
- `get_absolute_url` - Build absolute URLs
- `validate_image` - Image validation with size limits
- `request_is_bound` - Check if request has data

#### Configuration
- Pre-configured Django apps (`UTILS_APPS`)
- Pre-configured middleware (`AUDIT_MIDDLEWARE`)
- Automatic S3 validation
- JWT key file validation

#### Documentation
- Comprehensive README
- Detailed documentation for all modules
- 126 passing tests with full coverage
- CI/CD with GitHub Actions

### Dependencies
- Django 5.0+
- Python 3.11+
- boto3, celery, django-ninja, pydantic-settings
- django-auditlog, django-structlog
- PyJWT, jwcrypto, cryptography

[Unreleased]: https://github.com/oxiliere/oxutils/compare/v0.1.10...HEAD
[0.1.10]: https://github.com/oxiliere/oxutils/compare/v0.1.9...v0.1.10
[0.1.3]: https://github.com/oxiliere/oxutils/compare/v0.1.0...v0.1.3
[0.1.0]: https://github.com/oxiliere/oxutils/releases/tag/v0.1.0
