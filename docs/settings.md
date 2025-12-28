# Settings & Configuration

**Pydantic-based configuration with automatic validation**

## Overview

OxUtils uses Pydantic settings for type-safe, validated configuration via environment variables. All settings use the `OXI_` prefix and are automatically validated on startup.

## Quick Start

```bash
# .env
OXI_SERVICE_NAME=my-service
OXI_SITE_NAME=MyApp
OXI_SITE_DOMAIN=myapp.com
OXI_JWT_VERIFYING_KEY=/path/to/public_key.pem
OXI_LOG_FILE_PATH=logs/app.log
```

```python
# settings.py
from oxutils.conf import UTILS_APPS, AUDIT_MIDDLEWARE
from oxutils.settings import oxi_settings

INSTALLED_APPS = [*UTILS_APPS, 'myapp']
MIDDLEWARE = [*AUDIT_MIDDLEWARE, ...]

# Access settings
print(oxi_settings.service_name)  # 'my-service'
```

## Configuration Reference

### Service Identification

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OXI_SERVICE_NAME` | string | `'Oxutils'` | Service name for identification in logs and tokens. |
| `OXI_SITE_NAME` | string | `'Oxiliere'` | Application/site name. |
| `OXI_SITE_DOMAIN` | string | `'oxiliere.com'` | Primary site domain. |
| `OXI_MULTITENANCY` | boolean | `False` | Enable multitenancy support. |

### JWT Authentication

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OXI_JWT_SIGNING_KEY` | string | `None` | Path to RSA private key (PEM) for signing tokens. |
| `OXI_JWT_VERIFYING_KEY` | string | `None` | Path to RSA public key (PEM) for verifying tokens. |
| `OXI_JWT_JWKS_URL` | string | `None` | Remote JWKS URL (optional, used by ninja-jwt). |
| `OXI_JWT_ALGORITHM` | string | `'RS256'` | JWT signing algorithm. |
| `OXI_JWT_ACCESS_TOKEN_KEY` | string | `'access'` | Token type for user access tokens. |
| `OXI_JWT_SERVICE_TOKEN_KEY` | string | `'service'` | Token type for service tokens. |
| `OXI_JWT_ORG_ACCESS_TOKEN_KEY` | string | `'org_access'` | Token type for organization tokens. |
| `OXI_JWT_ACCESS_TOKEN_LIFETIME` | int | `15` | Access token lifetime in minutes. |
| `OXI_JWT_SERVICE_TOKEN_LIFETIME` | int | `3` | Service token lifetime in minutes. |
| `OXI_JWT_ORG_ACCESS_TOKEN_LIFETIME` | int | `60` | Organization token lifetime in minutes. |

### Audit Logging

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OXI_LOG_ACCESS` | boolean | `False` | Enable access logging for audit trail. |
| `OXI_RETENTION_DELAY` | int | `7` | Log retention period in days. |

### Application Logging

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OXI_LOG_FILE_PATH` | string | `'logs/oxiliere.log'` | Path to JSON log file. Directory must exist. |

### S3 Storage - Static Files

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OXI_USE_STATIC_S3` | boolean | `False` | Enable S3 for static files (CSS, JS, images). |
| `OXI_STATIC_ACCESS_KEY_ID` | string | `None` | AWS access key ID. Required if `USE_STATIC_S3=True`. |
| `OXI_STATIC_SECRET_ACCESS_KEY` | string | `None` | AWS secret access key. Required if `USE_STATIC_S3=True`. |
| `OXI_STATIC_STORAGE_BUCKET_NAME` | string | `None` | S3 bucket name. Required if `USE_STATIC_S3=True`. |
| `OXI_STATIC_S3_CUSTOM_DOMAIN` | string | `None` | CDN/CloudFront domain. Required if `USE_STATIC_S3=True`. |
| `OXI_STATIC_LOCATION` | string | `'static'` | Folder path within bucket. |
| `OXI_STATIC_DEFAULT_ACL` | string | `'public-read'` | Default ACL for uploaded files. |
| `OXI_STATIC_STORAGE` | string | `'oxutils.s3.storages.StaticStorage'` | Storage backend class. |

### S3 Storage - Public Media

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OXI_USE_DEFAULT_S3` | boolean | `False` | Enable S3 for public media files (user uploads). |
| `OXI_USE_STATIC_S3_AS_DEFAULT` | boolean | `False` | Reuse static S3 credentials for media. Requires `USE_STATIC_S3=True`. |
| `OXI_DEFAULT_S3_ACCESS_KEY_ID` | string | `None` | AWS access key ID. Required if `USE_DEFAULT_S3=True` and not reusing static. |
| `OXI_DEFAULT_S3_SECRET_ACCESS_KEY` | string | `None` | AWS secret access key. Required if `USE_DEFAULT_S3=True` and not reusing static. |
| `OXI_DEFAULT_S3_STORAGE_BUCKET_NAME` | string | `None` | S3 bucket name. Required if `USE_DEFAULT_S3=True` and not reusing static. |
| `OXI_DEFAULT_S3_CUSTOM_DOMAIN` | string | `None` | CDN/CloudFront domain. Required if `USE_DEFAULT_S3=True` and not reusing static. |
| `OXI_DEFAULT_S3_LOCATION` | string | `'media'` | Folder path within bucket. |
| `OXI_DEFAULT_S3_DEFAULT_ACL` | string | `'public-read'` | Default ACL for uploaded files. |
| `OXI_DEFAULT_S3_STORAGE` | string | `'oxutils.s3.storages.PublicMediaStorage'` | Storage backend class. |

### S3 Storage - Private Media

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OXI_USE_PRIVATE_S3` | boolean | `False` | Enable S3 for private/sensitive files. |
| `OXI_PRIVATE_S3_ACCESS_KEY_ID` | string | `None` | AWS access key ID. Required if `USE_PRIVATE_S3=True`. |
| `OXI_PRIVATE_S3_SECRET_ACCESS_KEY` | string | `None` | AWS secret access key. Required if `USE_PRIVATE_S3=True`. |
| `OXI_PRIVATE_S3_STORAGE_BUCKET_NAME` | string | `None` | S3 bucket name. Required if `USE_PRIVATE_S3=True`. |
| `OXI_PRIVATE_S3_CUSTOM_DOMAIN` | string | `None` | CDN/CloudFront domain. Required if `USE_PRIVATE_S3=True`. |
| `OXI_PRIVATE_S3_LOCATION` | string | `'private'` | Folder path within bucket. |
| `OXI_PRIVATE_S3_DEFAULT_ACL` | string | `'private'` | Default ACL for uploaded files. |
| `OXI_PRIVATE_S3_STORAGE` | string | `'oxutils.s3.storages.PrivateMediaStorage'` | Storage backend class. |

### S3 Storage - Logs

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OXI_USE_LOG_S3` | boolean | `False` | Enable S3 for log storage. |
| `OXI_USE_PRIVATE_S3_AS_LOG` | boolean | `False` | Reuse private S3 credentials for logs. Requires `USE_PRIVATE_S3=True`. |
| `OXI_LOG_S3_ACCESS_KEY_ID` | string | `None` | AWS access key ID. Required if `USE_LOG_S3=True` and not reusing private. |
| `OXI_LOG_S3_SECRET_ACCESS_KEY` | string | `None` | AWS secret access key. Required if `USE_LOG_S3=True` and not reusing private. |
| `OXI_LOG_S3_STORAGE_BUCKET_NAME` | string | `None` | S3 bucket name. Required if `USE_LOG_S3=True` and not reusing private. |
| `OXI_LOG_S3_CUSTOM_DOMAIN` | string | `None` | CDN/CloudFront domain. Required if `USE_LOG_S3=True` and not reusing private. |
| `OXI_LOG_S3_LOCATION` | string | `'oxi_logs'` | Folder path within bucket. |
| `OXI_LOG_S3_DEFAULT_ACL` | string | `'private'` | Default ACL for uploaded files. |
| `OXI_LOG_S3_STORAGE` | string | `'oxutils.s3.storages.LogStorage'` | Storage backend class. |

## Usage

### Accessing Settings

```python
from oxutils.settings import oxi_settings

# Service info
service_name = oxi_settings.service_name
is_multitenant = oxi_settings.multitenancy

# JWT
jwt_algorithm = oxi_settings.jwt_algorithm
access_lifetime = oxi_settings.jwt_access_token_lifetime

# S3
if oxi_settings.use_static_s3:
    static_url = oxi_settings.get_static_storage_url()
    print(f"Static files: {static_url}")

# Logging
log_path = oxi_settings.log_file_path
```

### Django Integration

```python
# settings.py
from oxutils.settings import oxi_settings

# Configure S3 storages
oxi_settings.write_django_settings(sys.modules[__name__])

# This sets:
# - STATIC_URL and STATICFILES_STORAGE (if use_static_s3)
# - MEDIA_URL and DEFAULT_FILE_STORAGE (if use_default_s3)
# - PRIVATE_MEDIA_LOCATION and PRIVATE_FILE_STORAGE (if use_private_s3)
```

### Helper Methods

```python
from oxutils.settings import oxi_settings

# Get storage URLs
static_url = oxi_settings.get_static_storage_url()
media_url = oxi_settings.get_default_storage_url()
private_url = oxi_settings.get_private_storage_url()
log_url = oxi_settings.get_log_storage_url()
```

## Environment Examples

### Development

```bash
# Service
OXI_SERVICE_NAME=myapp-dev
OXI_SITE_NAME=MyApp Dev
OXI_SITE_DOMAIN=localhost:8000

# JWT (local keys)
OXI_JWT_SIGNING_KEY=/path/to/keys/private_key.pem
OXI_JWT_VERIFYING_KEY=/path/to/keys/public_key.pem
OXI_JWT_ALGORITHM=RS256

# Logging
OXI_LOG_FILE_PATH=logs/dev.log

# S3 disabled
OXI_USE_STATIC_S3=False
OXI_USE_DEFAULT_S3=False
```

### Production

```bash
# Service
OXI_SERVICE_NAME=myapp
OXI_SITE_NAME=MyApp
OXI_SITE_DOMAIN=myapp.com
OXI_MULTITENANCY=True

# JWT (remote JWKS)
OXI_JWT_JWKS_URL=https://auth.myapp.com/.well-known/jwks.json
OXI_JWT_VERIFYING_KEY=/etc/keys/public_key.pem
OXI_JWT_ALGORITHM=RS256
OXI_JWT_ACCESS_TOKEN_LIFETIME=15
OXI_JWT_SERVICE_TOKEN_LIFETIME=3

# Audit
OXI_LOG_ACCESS=True
OXI_RETENTION_DELAY=30

# Logging
OXI_LOG_FILE_PATH=/var/log/myapp/app.log

# S3 Static
OXI_USE_STATIC_S3=True
OXI_STATIC_ACCESS_KEY_ID=AKIA...
OXI_STATIC_SECRET_ACCESS_KEY=secret...
OXI_STATIC_STORAGE_BUCKET_NAME=myapp-static
OXI_STATIC_S3_CUSTOM_DOMAIN=cdn.myapp.com
OXI_STATIC_LOCATION=static

# S3 Media (reuse static credentials)
OXI_USE_DEFAULT_S3=True
OXI_USE_STATIC_S3_AS_DEFAULT=True
OXI_DEFAULT_S3_LOCATION=media

# S3 Private
OXI_USE_PRIVATE_S3=True
OXI_PRIVATE_S3_ACCESS_KEY_ID=AKIA...
OXI_PRIVATE_S3_SECRET_ACCESS_KEY=secret...
OXI_PRIVATE_S3_STORAGE_BUCKET_NAME=myapp-private
OXI_PRIVATE_S3_CUSTOM_DOMAIN=private.myapp.com
OXI_PRIVATE_S3_LOCATION=private
OXI_PRIVATE_S3_DEFAULT_ACL=private

# S3 Logs (reuse private credentials)
OXI_USE_LOG_S3=True
OXI_USE_PRIVATE_S3_AS_LOG=True
OXI_LOG_S3_LOCATION=logs
```

## Validation

Settings are automatically validated on application startup using Pydantic validators:

### S3 Validation

When enabling S3 storage, all required fields must be provided:
- `access_key_id`
- `secret_access_key`
- `storage_bucket_name`
- `custom_domain`

**Example error:**
```
ValueError: Missing required static S3 configuration: 
OXI_STATIC_ACCESS_KEY_ID, OXI_STATIC_STORAGE_BUCKET_NAME
```

### JWT Validation

JWT key files are validated for existence and readability:

**Example error:**
```
ValueError: JWT verifying key file not found at: /path/to/key.pem
```

### Dependency Validation

Certain settings require others to be enabled:

- `OXI_USE_STATIC_S3_AS_DEFAULT=True` requires `OXI_USE_STATIC_S3=True`
- `OXI_USE_PRIVATE_S3_AS_LOG=True` requires `OXI_USE_PRIVATE_S3=True`

**Example error:**
```
ValueError: OXI_USE_STATIC_S3_AS_DEFAULT requires OXI_USE_STATIC_S3 to be True
```

## Best Practices

1. **Use environment variables**: Never hardcode sensitive values in code
2. **Validate early**: Settings are validated on import, catching errors at startup
3. **Reuse credentials**: Use `USE_STATIC_S3_AS_DEFAULT` and `USE_PRIVATE_S3_AS_LOG` to reduce configuration
4. **Separate environments**: Use different `.env` files for dev/staging/prod
5. **Secure key storage**: Store JWT keys outside the repository
6. **Set appropriate lifetimes**: Short tokens for access, very short for services
7. **Enable audit logging**: Set `OXI_LOG_ACCESS=True` in production

## Related Docs

- [JWT](./jwt.md) - JWT authentication configuration
- [Logger](./logger.md) - Structured logging configuration
- [S3](./s3.md) - S3 storage backends
