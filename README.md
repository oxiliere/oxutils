# OxUtils

**Comprehensive utilities library for Django applications in the Oxiliere ecosystem.**

OxUtils provides a complete suite of tools for building production-ready Django applications with JWT authentication, S3 storage, structured logging, audit trails, and more.

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-4.0+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Features

### 🔐 Authentication & Security
- **JWT Authentication** - RS256 with JWKS support
- **Token Verification** - Automatic token validation and caching
- **Multi-tenant Support** - Organization-level token management

### 📦 Storage Management
- **S3 Integration** - Four specialized storage backends
  - Static files (CSS, JS, images)
  - Public media (user uploads)
  - Private media (sensitive documents with presigned URLs)
  - Audit logs (automatic service organization)
- **CDN Support** - CloudFront integration
- **Automatic Validation** - Configuration validation on startup

### 📝 Logging & Monitoring
- **Structured Logging** - JSON-formatted logs with `structlog`
- **Correlation ID Tracking** - Request tracing across services
- **Multiple Formatters** - JSON, key-value, and colored console
- **Automatic Context** - User, domain, and service information

### 🔍 Audit System
- **Change Tracking** - Automatic model change logging
- **Data Masking** - Sensitive field protection
- **Log Export** - Compressed ZIP exports to S3
- **Retention Management** - Configurable retention policies

### ⚙️ Task Processing
- **Celery Integration** - Pre-configured with structured logging
- **Auto-discovery** - Automatic task discovery
- **Correlation IDs** - Request tracking in async tasks

### 🛠️ Developer Tools
- **Django Mixins** - UUID, timestamps, user tracking, and more
- **Custom Exceptions** - Standardized error handling
- **Utility Functions** - URL building, request validation, image validation
- **Type Safety** - Full type hints support

---

## Installation

```bash
pip install oxutils
```

Or with uv:

```bash
uv add oxutils
```

---

## Quick Start

### 1. Basic Setup

```python
# settings.py
from oxutils.conf import UTILS_APPS, AUDIT_MIDDLEWARE
from oxutils.settings import oxi_settings

# Add OxUtils apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ...
    *UTILS_APPS,  # django_structlog, auditlog, cid, django_celery_results
    'myapp',
]

# Add middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    *AUDIT_MIDDLEWARE,  # CID, Auditlog, RequestMiddleware
    'django.middleware.common.CommonMiddleware',
    # ...
]

# Configure service
OXI_SERVICE_NAME = 'my-service'
```

### 2. Environment Variables

```bash
# .env
OXI_SERVICE_NAME=my-service

# JWT Authentication
OXI_JWT_JWKS_URL=https://auth.example.com/.well-known/jwks.json

# S3 Storage
OXI_USE_STATIC_S3=True
OXI_STATIC_STORAGE_BUCKET_NAME=my-bucket
OXI_STATIC_S3_CUSTOM_DOMAIN=cdn.example.com

# Audit Logging
OXI_LOG_ACCESS=True
OXI_RETENTION_DELAY=30
```

### 3. Use in Your Code

```python
# JWT Authentication
from oxutils.jwt.client import verify_token

payload = verify_token(token)
user_id = payload.get('sub')

# Structured Logging
import structlog
logger = structlog.get_logger(__name__)

logger.info("user_logged_in", user_id=user_id, email=email)

# S3 Storage
from oxutils.s3.storages import PrivateMediaStorage

class Document(models.Model):
    file = models.FileField(storage=PrivateMediaStorage())

# Custom Exceptions
from oxutils.exceptions import NotFoundException

if not user:
    raise NotFoundException(detail="User not found")

# Model Mixins
from oxutils.models.base import BaseModelMixin

class Product(BaseModelMixin):  # UUID, timestamps, active status
    name = models.CharField(max_length=255)
```

---

## Documentation

### Core Components

- **[Settings & Configuration](docs/settings.md)** - Complete configuration reference
- **[Mixins](docs/mixins.md)** - Model, service, and schema mixins
- **[Enums](docs/enums.md)** - Standardized enumerations

### Authentication & Security

- **[JWT Authentication](docs/jwt.md)** - Token verification and JWKS integration
- **[Exceptions](docs/misc.md)** - Custom exceptions and error handling

### Storage & Files

- **[S3 Storage](docs/s3.md)** - Four storage backends for different use cases
- **[Audit System](docs/audit.md)** - Change tracking and log export

### Logging & Monitoring

- **[Structured Logging](docs/logger.md)** - JSON logs with correlation IDs
- **[Celery Integration](docs/celery.md)** - Async task processing

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        OxUtils                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     JWT      │  │   Storage    │  │   Logging    │     │
│  │              │  │              │  │              │     │
│  │ • JWKS       │  │ • Static     │  │ • Structlog  │     │
│  │ • RS256      │  │ • Media      │  │ • JSON       │     │
│  │ • Caching    │  │ • Private    │  │ • CID        │     │
│  │              │  │ • Logs       │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Audit     │  │   Celery     │  │   Mixins     │     │
│  │              │  │              │  │              │     │
│  │ • Tracking   │  │ • Tasks      │  │ • Models     │     │
│  │ • Masking    │  │ • Logging    │  │ • Services   │     │
│  │ • Export     │  │ • CID        │  │ • Schemas    │     │
│  │              │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration Examples

### Development

```bash
# .env.development
OXI_SERVICE_NAME=my-service-dev
OXI_JWT_VERIFYING_KEY=./keys/public_key.pem
OXI_LOG_ACCESS=True
OXI_USE_STATIC_S3=False
```

### Production

```bash
# .env.production
OXI_SERVICE_NAME=my-service
OXI_JWT_JWKS_URL=https://auth.example.com/.well-known/jwks.json
OXI_LOG_ACCESS=True
OXI_RETENTION_DELAY=90

# S3 Storage
OXI_USE_STATIC_S3=True
OXI_STATIC_STORAGE_BUCKET_NAME=prod-static
OXI_STATIC_S3_CUSTOM_DOMAIN=cdn.example.com

OXI_USE_PRIVATE_S3=True
OXI_PRIVATE_S3_STORAGE_BUCKET_NAME=prod-private
OXI_PRIVATE_S3_DEFAULT_ACL=private

OXI_USE_LOG_S3=True
OXI_USE_PRIVATE_S3_AS_LOG=True
```

---

## Usage Examples

### JWT Authentication

```python
from ninja import Router
from ninja.security import HttpBearer
from oxutils.jwt.client import verify_token

class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = verify_token(token)
            return payload
        except:
            return None

api = NinjaAPI(auth=JWTAuth())

@api.get("/protected")
def protected_endpoint(request):
    user_id = request.auth.get('sub')
    return {"user_id": user_id}
```

### S3 File Upload

```python
from django.db import models
from oxutils.s3.storages import PrivateMediaStorage

class Invoice(models.Model):
    pdf = models.FileField(
        storage=PrivateMediaStorage(),
        upload_to='invoices/%Y/%m/'
    )
    
    def get_download_url(self):
        # Returns presigned URL (valid 1 hour)
        return self.pdf.url
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger(__name__)

def process_order(order_id: str):
    logger.info("order_processing_started", order_id=order_id)
    
    try:
        order = Order.objects.get(id=order_id)
        order.process()
        
        logger.info(
            "order_processed",
            order_id=order_id,
            total=float(order.total)
        )
    except Exception as e:
        logger.error(
            "order_processing_failed",
            order_id=order_id,
            error=str(e),
            exc_info=True
        )
        raise
```

### Audit Log Export

```python
from oxutils.audit.export import export_logs_from_date
from datetime import datetime, timedelta

# Export last 7 days
from_date = datetime.now() - timedelta(days=7)
export = export_logs_from_date(from_date=from_date)

print(f"Exported {export.size} bytes to {export.data.url}")
```

### Model Mixins

```python
from django.db import models
from oxutils.models.base import BaseModelMixin, NameMixin

class Product(BaseModelMixin, NameMixin):
    """
    Product with:
    - UUID primary key (from BaseModelMixin)
    - created_at, updated_at (from BaseModelMixin)
    - is_active (from BaseModelMixin)
    - name, description (from NameMixin)
    """
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
```

### Custom Exceptions

```python
from oxutils.exceptions import (
    NotFoundException,
    ValidationException,
    PermissionDeniedException
)

@router.get("/users/{user_id}")
def get_user(request, user_id: str):
    # Check permissions
    if not request.user.is_authenticated:
        raise PermissionDeniedException()
    
    # Get user
    try:
        user = User.objects.get(id=user_id)
        return user
    except User.DoesNotExist:
        raise NotFoundException(detail="User not found")
```

---

## Requirements

- Python 3.10+
- Django 4.0+
- PostgreSQL (recommended) or MySQL

### Core Dependencies

```
django>=4.0
pydantic>=2.0
pydantic-settings>=2.0
structlog>=23.0
django-structlog>=5.0
django-auditlog>=2.0
django-cid>=2.0
PyJWT>=2.8
jwcrypto>=1.5
django-storages>=1.14
boto3>=1.28
celery>=5.3
redis>=5.0
```

---

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/oxiliere/oxutils.git
cd oxutils

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
mypy .
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=oxutils --cov-report=html

# Run specific test file
pytest tests/test_jwt.py

# Run with verbose output
pytest -v
```

---

## Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Write tests** for your changes
4. **Ensure tests pass** (`pytest`)
5. **Commit your changes** (`git commit -m 'Add amazing feature'`)
6. **Push to the branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public functions
- Keep functions focused and small
- Write tests for new features

---

## Changelog

### Version 1.0.0 (Current)

#### Features
- JWT authentication with JWKS support
- Four S3 storage backends
- Structured logging with correlation IDs
- Audit system with log export
- Celery integration
- Django model mixins
- Custom exceptions
- Utility functions

#### Components
- Settings management with Pydantic
- Pre-configured apps and middleware
- Automatic validation
- Comprehensive documentation

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

### Documentation
- [Complete Documentation](docs/)
- [Configuration Guide](docs/settings.md)
- [API Reference](docs/)

### Contact
- **Email**: dev@oxiliere.com
- **Issues**: [GitHub Issues](https://github.com/oxiliere/oxutils/issues)
- **Discussions**: [GitHub Discussions](https://github.com/oxiliere/oxutils/discussions)

---

## Acknowledgments

Built with ❤️ by the Oxiliere team.

Special thanks to:
- Django community
- django-structlog
- django-auditlog
- Pydantic
- All contributors

---

**Made with ❤️ for the Oxiliere ecosystem**
