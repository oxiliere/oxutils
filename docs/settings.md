# Settings & Configuration Documentation

## Overview

OxUtils provides a centralized configuration system using Pydantic settings with automatic validation, environment variable support, and Django integration. The system manages all OxUtils components including JWT authentication, S3 storage, audit logging, and Celery configuration.

### Key Features

- **Pydantic-based**: Type-safe settings with automatic validation
- **Environment Variables**: All settings configurable via environment variables
- **Automatic Validation**: Built-in validation for S3 and JWT configurations
- **Django Integration**: Seamless integration with Django settings
- **Centralized Management**: Single source of truth for all configurations
- **Default Values**: Sensible defaults for all optional settings
- **Clear Error Messages**: Descriptive validation errors

---

## Table of Contents

- [Architecture](#architecture)
- [Installation & Setup](#installation--setup)
- [Configuration Reference](#configuration-reference)
  - [Service Settings](#service-settings)
  - [JWT Settings](#jwt-settings)
  - [Audit Settings](#audit-settings)
  - [S3 Storage Settings](#s3-storage-settings)
- [Configuration Methods](#configuration-methods)
- [Validation](#validation)
- [Django Integration](#django-integration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Architecture

### Settings Structure

```
OxUtilsSettings (Pydantic BaseSettings)
├── Service Configuration
│   └── service_name
├── JWT Authentication
│   ├── jwt_signing_key
│   ├── jwt_verifying_key
│   ├── jwt_jwks_url
│   ├── jwt_access_token_key
│   └── jwt_org_access_token_key
├── Audit Logging
│   ├── log_access
│   └── retention_delay
└── S3 Storage (4 backends)
    ├── Static S3
    ├── Public Media S3
    ├── Private Media S3
    └── Log S3
```

### Configuration Flow

```
Environment Variables (.env)
         ↓
OXI_* prefix applied
         ↓
Pydantic Settings Loading
         ↓
Automatic Validation
         ↓
oxi_settings instance
         ↓
Django Settings Integration
```

---

## Installation & Setup

### Basic Setup

1. **Import settings in Django:**

```python
# settings.py
from oxutils.settings import oxi_settings

# Access settings
SERVICE_NAME = oxi_settings.service_name
JWT_JWKS_URL = oxi_settings.jwt_jwks_url
```

2. **Configure via environment variables:**

```bash
# .env file
OXI_SERVICE_NAME=my-service
OXI_JWT_JWKS_URL=https://auth.example.com/.well-known/jwks.json
OXI_USE_STATIC_S3=True
OXI_STATIC_STORAGE_BUCKET_NAME=my-bucket
```

3. **Import pre-configured apps and middleware:**

```python
# settings.py
from oxutils.conf import UTILS_APPS, AUDIT_MIDDLEWARE

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    # ...
    
    # OxUtils apps
    *UTILS_APPS,  # django_structlog, auditlog, cid, django_celery_results
    
    # Your apps
    'myapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    
    # OxUtils middleware
    *AUDIT_MIDDLEWARE,  # CID, Auditlog, RequestMiddleware
    
    'django.middleware.common.CommonMiddleware',
    # ...
]
```

---

## Configuration Reference

### Service Settings

| Setting | Type | Required | Default | Description |
|---------|------|----------|---------|-------------|
| `OXI_SERVICE_NAME` | `str` | **Yes** | - | Name of the service (used in logs, S3 paths) |

**Example:**
```bash
OXI_SERVICE_NAME=user-service
```

---

### JWT Settings

| Setting | Type | Required | Default | Description |
|---------|------|----------|---------|-------------|
| `OXI_JWT_SIGNING_KEY` | `str` | No | `None` | Path to private key for signing tokens |
| `OXI_JWT_VERIFYING_KEY` | `str` | No | `None` | Path to public key for verifying tokens |
| `OXI_JWT_JWKS_URL` | `str` | No | `None` | URL to fetch JWKS from auth server |
| `OXI_JWT_ACCESS_TOKEN_KEY` | `str` | No | `"access_token"` | Key name for access token in requests |
| `OXI_JWT_ORG_ACCESS_TOKEN_KEY` | `str` | No | `"org_access_token"` | Key name for organization token |

**Example:**
```bash
# JWKS-based authentication
OXI_JWT_JWKS_URL=https://auth.example.com/.well-known/jwks.json

# Local key authentication
OXI_JWT_VERIFYING_KEY=/path/to/public_key.pem
OXI_JWT_SIGNING_KEY=/path/to/private_key.pem

# Custom token keys
OXI_JWT_ACCESS_TOKEN_KEY=bearer_token
OXI_JWT_ORG_ACCESS_TOKEN_KEY=org_token
```

**Validation:**
- If `jwt_signing_key` or `jwt_verifying_key` is set, the file must exist
- File paths are validated at startup

---

### Audit Settings

| Setting | Type | Required | Default | Description |
|---------|------|----------|---------|-------------|
| `OXI_LOG_ACCESS` | `bool` | No | `False` | Enable logging of read operations |
| `OXI_RETENTION_DELAY` | `int` | No | `7` | Number of days to retain audit logs |

**Example:**
```bash
OXI_LOG_ACCESS=True
OXI_RETENTION_DELAY=30  # 30 days
```

---

### S3 Storage Settings

#### Static S3 Settings

| Setting | Type | Required | Default | Description |
|---------|------|----------|---------|-------------|
| `OXI_USE_STATIC_S3` | `bool` | No | `False` | Enable static S3 storage |
| `OXI_STATIC_ACCESS_KEY_ID` | `str` | If enabled | `None` | AWS access key ID |
| `OXI_STATIC_SECRET_ACCESS_KEY` | `str` | If enabled | `None` | AWS secret access key |
| `OXI_STATIC_STORAGE_BUCKET_NAME` | `str` | If enabled | `None` | S3 bucket name |
| `OXI_STATIC_DEFAULT_ACL` | `str` | No | `"public-read"` | Default ACL for files |
| `OXI_STATIC_S3_CUSTOM_DOMAIN` | `str` | If enabled | `None` | Custom domain (CDN) |
| `OXI_STATIC_LOCATION` | `str` | No | `"static"` | Folder path in bucket |
| `OXI_STATIC_STORAGE` | `str` | No | `"oxutils.s3.storages.StaticStorage"` | Storage class path |

**Example:**
```bash
OXI_USE_STATIC_S3=True
OXI_STATIC_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
OXI_STATIC_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
OXI_STATIC_STORAGE_BUCKET_NAME=my-static-bucket
OXI_STATIC_S3_CUSTOM_DOMAIN=d111111abcdef8.cloudfront.net
OXI_STATIC_LOCATION=static
OXI_STATIC_DEFAULT_ACL=public-read
```

#### Public Media S3 Settings

| Setting | Type | Required | Default | Description |
|---------|------|----------|---------|-------------|
| `OXI_USE_DEFAULT_S3` | `bool` | No | `False` | Enable public media S3 storage |
| `OXI_USE_STATIC_S3_AS_DEFAULT` | `bool` | No | `False` | Reuse static S3 credentials |
| `OXI_DEFAULT_S3_ACCESS_KEY_ID` | `str` | If enabled | `None` | AWS access key ID |
| `OXI_DEFAULT_S3_SECRET_ACCESS_KEY` | `str` | If enabled | `None` | AWS secret access key |
| `OXI_DEFAULT_S3_STORAGE_BUCKET_NAME` | `str` | If enabled | `None` | S3 bucket name |
| `OXI_DEFAULT_S3_DEFAULT_ACL` | `str` | No | `"public-read"` | Default ACL for files |
| `OXI_DEFAULT_S3_S3_CUSTOM_DOMAIN` | `str` | If enabled | `None` | Custom domain (CDN) |
| `OXI_DEFAULT_S3_LOCATION` | `str` | No | `"media"` | Folder path in bucket |
| `OXI_DEFAULT_S3_STORAGE` | `str` | No | `"oxutils.s3.storages.PublicMediaStorage"` | Storage class path |

**Example:**
```bash
OXI_USE_DEFAULT_S3=True
OXI_DEFAULT_S3_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
OXI_DEFAULT_S3_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
OXI_DEFAULT_S3_STORAGE_BUCKET_NAME=my-media-bucket
OXI_DEFAULT_S3_S3_CUSTOM_DOMAIN=d222222abcdef8.cloudfront.net
OXI_DEFAULT_S3_LOCATION=media

# Or reuse static S3 credentials
OXI_USE_STATIC_S3_AS_DEFAULT=True
```

#### Private Media S3 Settings

| Setting | Type | Required | Default | Description |
|---------|------|----------|---------|-------------|
| `OXI_USE_PRIVATE_S3` | `bool` | No | `False` | Enable private media S3 storage |
| `OXI_PRIVATE_S3_ACCESS_KEY_ID` | `str` | If enabled | `None` | AWS access key ID |
| `OXI_PRIVATE_S3_SECRET_ACCESS_KEY` | `str` | If enabled | `None` | AWS secret access key |
| `OXI_PRIVATE_S3_STORAGE_BUCKET_NAME` | `str` | If enabled | `None` | S3 bucket name |
| `OXI_PRIVATE_S3_DEFAULT_ACL` | `str` | No | `"private"` | Default ACL for files |
| `OXI_PRIVATE_S3_S3_CUSTOM_DOMAIN` | `str` | If enabled | `None` | Custom domain |
| `OXI_PRIVATE_S3_LOCATION` | `str` | No | `"private"` | Folder path in bucket |
| `OXI_PRIVATE_S3_STORAGE` | `str` | No | `"oxutils.s3.storages.PrivateMediaStorage"` | Storage class path |

**Example:**
```bash
OXI_USE_PRIVATE_S3=True
OXI_PRIVATE_S3_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
OXI_PRIVATE_S3_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
OXI_PRIVATE_S3_STORAGE_BUCKET_NAME=my-private-bucket
OXI_PRIVATE_S3_S3_CUSTOM_DOMAIN=my-private-bucket.s3.amazonaws.com
OXI_PRIVATE_S3_LOCATION=private
OXI_PRIVATE_S3_DEFAULT_ACL=private
```

#### Log S3 Settings

| Setting | Type | Required | Default | Description |
|---------|------|----------|---------|-------------|
| `OXI_USE_LOG_S3` | `bool` | No | `False` | Enable log S3 storage |
| `OXI_USE_PRIVATE_S3_AS_LOG` | `bool` | No | `False` | Reuse private S3 credentials |
| `OXI_LOG_S3_ACCESS_KEY_ID` | `str` | If enabled | `None` | AWS access key ID |
| `OXI_LOG_S3_SECRET_ACCESS_KEY` | `str` | If enabled | `None` | AWS secret access key |
| `OXI_LOG_S3_STORAGE_BUCKET_NAME` | `str` | If enabled | `None` | S3 bucket name |
| `OXI_LOG_S3_DEFAULT_ACL` | `str` | No | `"private"` | Default ACL for files |
| `OXI_LOG_S3_S3_CUSTOM_DOMAIN` | `str` | If enabled | `None` | Custom domain |
| `OXI_LOG_S3_LOCATION` | `str` | No | `"oxi_logs"` | Folder path in bucket |
| `OXI_LOG_S3_STORAGE` | `str` | No | `"oxutils.s3.storages.LogStorage"` | Storage class path |

**Example:**
```bash
OXI_USE_LOG_S3=True
OXI_LOG_S3_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
OXI_LOG_S3_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
OXI_LOG_S3_STORAGE_BUCKET_NAME=my-logs-bucket
OXI_LOG_S3_S3_CUSTOM_DOMAIN=my-logs-bucket.s3.amazonaws.com
OXI_LOG_S3_LOCATION=oxi_logs

# Or reuse private S3 credentials
OXI_USE_PRIVATE_S3_AS_LOG=True
```

---

## Configuration Methods

### Method 1: Environment Variables

**Recommended for production**

```bash
# .env file
OXI_SERVICE_NAME=my-service
OXI_JWT_JWKS_URL=https://auth.example.com/.well-known/jwks.json
OXI_USE_STATIC_S3=True
OXI_STATIC_STORAGE_BUCKET_NAME=my-bucket
```

### Method 2: Django Settings Override

```python
# settings.py
from oxutils.settings import oxi_settings

# Override specific settings
oxi_settings.service_name = 'my-service'
oxi_settings.log_access = True
```

### Method 3: Programmatic Configuration

```python
from oxutils.settings import OxUtilsSettings

# Create custom settings instance
custom_settings = OxUtilsSettings(
    service_name='my-service',
    jwt_jwks_url='https://auth.example.com/.well-known/jwks.json',
    use_static_s3=True,
    static_storage_bucket_name='my-bucket'
)
```

---

## Validation

### Automatic Validation

The settings system automatically validates configurations at startup.

#### S3 Validation

When S3 storage is enabled, the following fields are validated:

```python
# Required fields for each S3 backend
- access_key_id
- secret_access_key
- storage_bucket_name
- s3_custom_domain
```

**Example Error:**
```
ValueError: Missing required static S3 configuration: OXI_STATIC_ACCESS_KEY_ID, OXI_STATIC_S3_CUSTOM_DOMAIN
```

#### JWT Validation

When JWT keys are configured, file existence is validated:

```python
# Validates that key files exist and are readable
- jwt_signing_key
- jwt_verifying_key
```

**Example Error:**
```
ValueError: JWT verifying key file not found at: /path/to/key.pem
```

#### Dependency Validation

Settings with dependencies are validated:

```python
# OXI_USE_STATIC_S3_AS_DEFAULT requires OXI_USE_STATIC_S3=True
if use_static_s3_as_default and not use_static_s3:
    raise ValueError("OXI_USE_STATIC_S3_AS_DEFAULT requires OXI_USE_STATIC_S3 to be True")

# OXI_USE_PRIVATE_S3_AS_LOG requires OXI_USE_PRIVATE_S3=True
if use_private_s3_as_log and not use_private_s3:
    raise ValueError("OXI_USE_PRIVATE_S3_AS_LOG requires OXI_USE_PRIVATE_S3 to be True")
```

### Manual Validation

```python
from oxutils.settings import oxi_settings

# Validate settings manually
try:
    # Access settings to trigger validation
    service_name = oxi_settings.service_name
    
    # Validate S3 configuration
    if oxi_settings.use_static_s3:
        url = oxi_settings.get_static_storage_url()
        print(f"Static URL: {url}")
        
except ValueError as e:
    print(f"Configuration error: {e}")
```

---

## Django Integration

### Pre-configured Apps

```python
# oxutils.conf.UTILS_APPS
UTILS_APPS = (
    'django_structlog',      # Structured logging
    'auditlog',              # Audit logging
    'cid.apps.CidAppConfig', # Correlation ID
    'django_celery_results', # Celery results
)
```

**Usage:**
```python
# settings.py
from oxutils.conf import UTILS_APPS

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    # ...
    
    # OxUtils apps
    *UTILS_APPS,
    
    # Your apps
    'myapp',
]
```

### Pre-configured Middleware

```python
# oxutils.conf.AUDIT_MIDDLEWARE
AUDIT_MIDDLEWARE = (
    'cid.middleware.CidMiddleware',                    # Correlation ID
    'auditlog.middleware.AuditlogMiddleware',          # Audit logging
    'django_structlog.middlewares.RequestMiddleware',  # Structured logging
)
```

**Usage:**
```python
# settings.py
from oxutils.conf import AUDIT_MIDDLEWARE

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    
    # OxUtils middleware (should be early in the stack)
    *AUDIT_MIDDLEWARE,
    
    'django.middleware.common.CommonMiddleware',
    # ...
]
```

### Automatic Django Settings Configuration

```python
# settings.py
from oxutils.settings import oxi_settings
import sys

# Automatically configure Django settings
oxi_settings.write_django_settings(sys.modules[__name__])

# This sets:
# - STATIC_URL and STATICFILES_STORAGE (if use_static_s3)
# - MEDIA_URL and DEFAULT_FILE_STORAGE (if use_default_s3)
# - PRIVATE_MEDIA_LOCATION and PRIVATE_FILE_STORAGE (if use_private_s3)
```

### Manual Django Settings Configuration

```python
# settings.py
from oxutils.settings import oxi_settings

# Static files
if oxi_settings.use_static_s3:
    STATIC_URL = oxi_settings.get_static_storage_url()
    STATICFILES_STORAGE = oxi_settings.static_storage

# Media files
if oxi_settings.use_default_s3:
    MEDIA_URL = oxi_settings.get_default_storage_url()
    DEFAULT_FILE_STORAGE = oxi_settings.default_s3_storage

# Private files
if oxi_settings.use_private_s3:
    PRIVATE_MEDIA_LOCATION = oxi_settings.private_s3_location
    PRIVATE_FILE_STORAGE = oxi_settings.private_s3_storage
```

---

## Best Practices

### 1. Use Environment Variables

**✅ Good - Environment variables:**
```bash
# .env
OXI_SERVICE_NAME=my-service
OXI_JWT_JWKS_URL=https://auth.example.com/.well-known/jwks.json
```

**❌ Bad - Hardcoded in settings:**
```python
# settings.py
oxi_settings.service_name = 'my-service'  # Don't hardcode
```

### 2. Separate Configurations by Environment

```bash
# .env.development
OXI_SERVICE_NAME=my-service-dev
OXI_USE_STATIC_S3=False

# .env.production
OXI_SERVICE_NAME=my-service
OXI_USE_STATIC_S3=True
OXI_STATIC_STORAGE_BUCKET_NAME=prod-bucket
```

### 3. Validate on Startup

```python
# settings.py or apps.py
from oxutils.settings import oxi_settings

def validate_configuration():
    """Validate configuration on startup."""
    required_settings = [
        ('service_name', oxi_settings.service_name),
    ]
    
    for name, value in required_settings:
        if not value:
            raise ValueError(f"Required setting {name} is not configured")

# In AppConfig
class MyAppConfig(AppConfig):
    def ready(self):
        validate_configuration()
```

### 4. Document Required Settings

```python
# README.md or docs/configuration.md
"""
Required Environment Variables:
- OXI_SERVICE_NAME: Name of the service
- OXI_JWT_JWKS_URL: JWKS URL for JWT verification

Optional Environment Variables:
- OXI_LOG_ACCESS: Enable access logging (default: False)
- OXI_RETENTION_DELAY: Log retention in days (default: 7)
"""
```

### 5. Use Type Hints

```python
from oxutils.settings import oxi_settings

def configure_service(service_name: str) -> None:
    """Configure service with type safety."""
    oxi_settings.service_name = service_name
```

### 6. Provide Defaults

```python
# Use Field() for defaults
from pydantic import Field

class MySettings(BaseSettings):
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
```

---

## Troubleshooting

### Common Issues

#### 1. "Missing required setting: service_name"

**Cause:** `OXI_SERVICE_NAME` not set

**Solution:**
```bash
export OXI_SERVICE_NAME=my-service
# or in .env
OXI_SERVICE_NAME=my-service
```

#### 2. "Missing required static S3 configuration"

**Cause:** S3 enabled but credentials missing

**Solution:**
```bash
export OXI_USE_STATIC_S3=True
export OXI_STATIC_ACCESS_KEY_ID=your-key
export OXI_STATIC_SECRET_ACCESS_KEY=your-secret
export OXI_STATIC_STORAGE_BUCKET_NAME=your-bucket
export OXI_STATIC_S3_CUSTOM_DOMAIN=your-domain
```

#### 3. "JWT verifying key file not found"

**Cause:** Key file path incorrect or file doesn't exist

**Solution:**
```bash
# Check file exists
ls -la /path/to/public_key.pem

# Set correct path
export OXI_JWT_VERIFYING_KEY=/correct/path/to/public_key.pem
```

#### 4. "OXI_USE_STATIC_S3_AS_DEFAULT requires OXI_USE_STATIC_S3 to be True"

**Cause:** Dependency not satisfied

**Solution:**
```bash
export OXI_USE_STATIC_S3=True
export OXI_USE_STATIC_S3_AS_DEFAULT=True
```

#### 5. Settings Not Loading

**Cause:** Environment variables not loaded

**Solution:**
```python
# Load .env file explicitly
from dotenv import load_dotenv
load_dotenv()

# Then import settings
from oxutils.settings import oxi_settings
```

### Debugging

**Print all settings:**
```python
from oxutils.settings import oxi_settings

print(oxi_settings.model_dump())
```

**Check specific setting:**
```python
from oxutils.settings import oxi_settings

print(f"Service: {oxi_settings.service_name}")
print(f"Static S3: {oxi_settings.use_static_s3}")
print(f"JWT JWKS URL: {oxi_settings.jwt_jwks_url}")
```

**Validate configuration:**
```python
from oxutils.settings import oxi_settings

try:
    # This triggers validation
    settings_dict = oxi_settings.model_dump()
    print("Configuration valid!")
except ValueError as e:
    print(f"Configuration error: {e}")
```

---

## Configuration Templates

### Development Configuration

```bash
# .env.development
OXI_SERVICE_NAME=my-service-dev

# JWT (local keys for development)
OXI_JWT_VERIFYING_KEY=./keys/public_key.pem
OXI_JWT_SIGNING_KEY=./keys/private_key.pem

# Audit
OXI_LOG_ACCESS=True
OXI_RETENTION_DELAY=7

# S3 (disabled for development)
OXI_USE_STATIC_S3=False
OXI_USE_DEFAULT_S3=False
OXI_USE_PRIVATE_S3=False
OXI_USE_LOG_S3=False
```

### Production Configuration

```bash
# .env.production
OXI_SERVICE_NAME=my-service

# JWT (JWKS for production)
OXI_JWT_JWKS_URL=https://auth.example.com/.well-known/jwks.json

# Audit
OXI_LOG_ACCESS=True
OXI_RETENTION_DELAY=90

# Static S3
OXI_USE_STATIC_S3=True
OXI_STATIC_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
OXI_STATIC_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
OXI_STATIC_STORAGE_BUCKET_NAME=prod-static-bucket
OXI_STATIC_S3_CUSTOM_DOMAIN=d111111abcdef8.cloudfront.net
OXI_STATIC_LOCATION=static
OXI_STATIC_DEFAULT_ACL=public-read

# Media S3 (reuse static credentials)
OXI_USE_DEFAULT_S3=True
OXI_USE_STATIC_S3_AS_DEFAULT=True
OXI_DEFAULT_S3_LOCATION=media

# Private S3
OXI_USE_PRIVATE_S3=True
OXI_PRIVATE_S3_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
OXI_PRIVATE_S3_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
OXI_PRIVATE_S3_STORAGE_BUCKET_NAME=prod-private-bucket
OXI_PRIVATE_S3_S3_CUSTOM_DOMAIN=prod-private-bucket.s3.amazonaws.com
OXI_PRIVATE_S3_LOCATION=private
OXI_PRIVATE_S3_DEFAULT_ACL=private

# Log S3 (reuse private credentials)
OXI_USE_LOG_S3=True
OXI_USE_PRIVATE_S3_AS_LOG=True
OXI_LOG_S3_LOCATION=oxi_logs
```

---

## Related Documentation

- [JWT Authentication](./jwt.md) - JWT configuration details
- [S3 Storage](./s3.md) - S3 storage configuration
- [Audit System](./audit.md) - Audit logging configuration
- [Structured Logging](./logger.md) - Logging configuration
- [Celery Integration](./celery.md) - Celery configuration
- [Mixins](./mixins.md) - Model and service mixins
- [Enums](./enums.md) - Standardized enumerations

---

## Support

For questions or issues regarding settings and configuration, please contact the Oxiliere development team or open an issue in the repository.
