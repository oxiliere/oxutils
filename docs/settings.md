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

# Logging
log_path = oxi_settings.log_file_path
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
```

## Validation

Settings are automatically validated on application startup using Pydantic validators:

### JWT Validation

JWT key files are validated for existence and readability:

**Example error:**
```
ValueError: JWT verifying key file not found at: /path/to/key.pem
```

## Best Practices

1. **Use environment variables**: Never hardcode sensitive values in code
2. **Validate early**: Settings are validated on import, catching errors at startup
3. **Separate environments**: Use different `.env` files for dev/staging/prod
4. **Secure keys**: Store JWT keys outside the repository
5. **Set appropriate lifetimes**: Short tokens for access, very short for services
6. **Enable audit logging**: Set `OXI_LOG_ACCESS=True` in production

## Related Docs

- [JWT](./jwt.md) - JWT authentication configuration
- [Logger](./logger.md) - Structured logging configuration
