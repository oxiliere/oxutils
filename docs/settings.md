# Settings & Configuration

**Pydantic-based configuration with automatic validation**

## Quick Start

```bash
# .env
OXI_SERVICE_NAME=my-service
OXI_JWT_JWKS_URL=https://auth.example.com/.well-known/jwks.json
OXI_USE_STATIC_S3=True
OXI_STATIC_STORAGE_BUCKET_NAME=my-bucket
```

```python
# settings.py
from oxutils.conf import UTILS_APPS, AUDIT_MIDDLEWARE
from oxutils.settings import oxi_settings

INSTALLED_APPS = [*UTILS_APPS, 'myapp']
MIDDLEWARE = [*AUDIT_MIDDLEWARE, ...]
```

## Configuration Reference

### Core Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `OXI_SERVICE_NAME` | - | **Required** - Service name |
| `OXI_LOG_ACCESS` | `False` | Enable access logging |
| `OXI_RETENTION_DELAY` | `7` | Log retention (days) |

### JWT Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `OXI_JWT_JWKS_URL` | `None` | JWKS endpoint URL |
| `OXI_JWT_VERIFYING_KEY` | `None` | Public key path |
| `OXI_JWT_SIGNING_KEY` | `None` | Private key path |
| `OXI_JWT_ACCESS_TOKEN_KEY` | `"access_token"` | Token key name |
| `OXI_JWT_ORG_ACCESS_TOKEN_KEY` | `"org_access_token"` | Org token key |

### S3 Storage Settings

**Static S3**

| Setting | Default | Description |
|---------|---------|-------------|
| `OXI_USE_STATIC_S3` | `False` | Enable static S3 |
| `OXI_STATIC_ACCESS_KEY_ID` | `None` | AWS access key |
| `OXI_STATIC_SECRET_ACCESS_KEY` | `None` | AWS secret key |
| `OXI_STATIC_STORAGE_BUCKET_NAME` | `None` | S3 bucket |
| `OXI_STATIC_S3_CUSTOM_DOMAIN` | `None` | CDN domain |
| `OXI_STATIC_LOCATION` | `"static"` | Folder path |
| `OXI_STATIC_DEFAULT_ACL` | `"public-read"` | File ACL |

**Public Media S3**

| Setting | Default | Description |
|---------|---------|-------------|
| `OXI_USE_DEFAULT_S3` | `False` | Enable media S3 |
| `OXI_USE_STATIC_S3_AS_DEFAULT` | `False` | Reuse static creds |
| `OXI_DEFAULT_S3_LOCATION` | `"media"` | Folder path |

**Private Media S3**

| Setting | Default | Description |
|---------|---------|-------------|
| `OXI_USE_PRIVATE_S3` | `False` | Enable private S3 |
| `OXI_PRIVATE_S3_LOCATION` | `"private"` | Folder path |
| `OXI_PRIVATE_S3_DEFAULT_ACL` | `"private"` | File ACL |

**Log S3**

| Setting | Default | Description |
|---------|---------|-------------|
| `OXI_USE_LOG_S3` | `False` | Enable log S3 |
| `OXI_USE_PRIVATE_S3_AS_LOG` | `False` | Reuse private creds |
| `OXI_LOG_S3_LOCATION` | `"oxi_logs"` | Folder path |

## Usage

```python
# Access settings
from oxutils.settings import oxi_settings

service = oxi_settings.service_name
jwks_url = oxi_settings.jwt_jwks_url
```

## Environment Examples

**Development**
```bash
OXI_SERVICE_NAME=my-service-dev
OXI_JWT_VERIFYING_KEY=./keys/public_key.pem
OXI_USE_STATIC_S3=False
```

**Production**
```bash
OXI_SERVICE_NAME=my-service
OXI_JWT_JWKS_URL=https://auth.example.com/.well-known/jwks.json
OXI_USE_STATIC_S3=True
OXI_STATIC_STORAGE_BUCKET_NAME=prod-bucket
OXI_STATIC_S3_CUSTOM_DOMAIN=cdn.example.com
```

## Validation

Settings are automatically validated on startup:
- S3: Requires access_key, secret_key, bucket_name, custom_domain
- JWT: Validates key file existence
- Dependencies: `USE_STATIC_S3_AS_DEFAULT` requires `USE_STATIC_S3=True`

## Related Docs

- [JWT](./jwt.md) - JWT configuration
- [S3](./s3.md) - S3 storage
- [Audit](./audit.md) - Audit logging
