# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- django-auditlog, django-structlog, django-cid
- PyJWT, jwcrypto, cryptography

[Unreleased]: https://github.com/oxiliere/oxutils/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/oxiliere/oxutils/releases/tag/v0.1.0
