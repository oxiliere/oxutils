# OxUtils

**Production-ready utilities for Django applications in the Oxiliere ecosystem.**

[![PyPI version](https://img.shields.io/pypi/v/oxutils.svg)](https://pypi.org/project/oxutils/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Django 5.0+](https://img.shields.io/badge/django-5.0+-green.svg)](https://www.djangoproject.com/)
[![Tests](https://img.shields.io/badge/tests-145%20passed-success.svg)](tests/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## Features

- 🔐 **JWT Authentication** - RS256 with JWKS caching
- 📦 **S3 Storage** - Static, media, private, and log backends
- 📝 **Structured Logging** - JSON logs with automatic request tracking
- 🔍 **Audit System** - Change tracking with S3 export
- ⚙️ **Celery Integration** - Pre-configured task processing
- 🛠️ **Django Mixins** - UUID, timestamps, user tracking
- ⚡ **Custom Exceptions** - Standardized API errors
- 🎨 **Context Processors** - Site name and domain for templates

---

## Installation

```bash
pip install oxutils
```

```bash
uv add oxutils
```

## Quick Start

### 1. Configure Django Settings

```python
# settings.py
from oxutils.conf import UTILS_APPS, AUDIT_MIDDLEWARE

INSTALLED_APPS = [
    *UTILS_APPS,  # structlog, auditlog, celery_results
    # your apps...
]

MIDDLEWARE = [
    *AUDIT_MIDDLEWARE,  # RequestMiddleware, Auditlog
    # your middleware...
]
```

### 2. Environment Variables

```bash
OXI_SERVICE_NAME=my-service
OXI_JWT_JWKS_URL=https://auth.example.com/.well-known/jwks.json
OXI_USE_STATIC_S3=True
OXI_STATIC_STORAGE_BUCKET_NAME=my-bucket
```

### 3. Usage Examples

```python
# JWT Authentication
from oxutils.jwt.client import verify_token
payload = verify_token(token)

# Structured Logging
import structlog
logger = structlog.get_logger(__name__)
logger.info("user_action", user_id=user_id)

# S3 Storage
from oxutils.s3.storages import PrivateMediaStorage
class Document(models.Model):
    file = models.FileField(storage=PrivateMediaStorage())

# Model Mixins
from oxutils.models.base import BaseModelMixin
class Product(BaseModelMixin):  # UUID + timestamps + is_active
    name = models.CharField(max_length=255)

# Custom Exceptions
from oxutils.exceptions import NotFoundException
raise NotFoundException(detail="User not found")

# Context Processors
# settings.py
TEMPLATES = [{
    'OPTIONS': {
        'context_processors': [
            'oxutils.context.site_name_processor.site_name',
        ],
    },
}]
# Now {{ site_name }} and {{ site_domain }} are available in templates
```

## Documentation

- **[Settings](docs/settings.md)** - Configuration reference
- **[JWT](docs/jwt.md)** - Authentication
- **[S3](docs/s3.md)** - Storage backends
- **[Audit](docs/audit.md)** - Change tracking
- **[Logging](docs/logger.md)** - Structured logs
- **[Mixins](docs/mixins.md)** - Model/service mixins
- **[Celery](docs/celery.md)** - Task processing

## Requirements

- Python 3.12+
- Django 5.0+
- PostgreSQL (recommended)

## Development

```bash
git clone https://github.com/oxiliere/oxutils.git
cd oxutils
uv sync
uv run pytest  # 145 tests
```

### Creating Migrations

To generate Django migrations for the audit module:

```bash
make migrations
# or
uv run make_migrations.py
```

See [MIGRATIONS.md](MIGRATIONS.md) for detailed documentation.

## Advanced Examples

### JWT with Django Ninja

```python
from ninja import NinjaAPI
from ninja.security import HttpBearer
from oxutils.jwt.client import verify_token

class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            return verify_token(token)
        except:
            return None

api = NinjaAPI(auth=JWTAuth())

@api.get("/protected")
def protected(request):
    return {"user_id": request.auth['sub']}
```

### Audit Log Export

```python
from oxutils.audit.export import export_logs_from_date
from datetime import datetime, timedelta

from_date = datetime.now() - timedelta(days=7)
export = export_logs_from_date(from_date=from_date)
print(f"Exported to {export.data.url}")
```

## License

Apache 2.0 License - see [LICENSE](LICENSE)

## Support

- **Issues**: [GitHub Issues](https://github.com/oxiliere/oxutils/issues)
- **Email**: dev@oxiliere.com

---

**Made with ❤️ by Oxiliere**
