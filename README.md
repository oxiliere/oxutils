# OxUtils

**Production-ready utilities for Django applications in the Oxiliere ecosystem.**

[![PyPI version](https://img.shields.io/pypi/v/oxutils.svg)](https://pypi.org/project/oxutils/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Django 5.0+](https://img.shields.io/badge/django-5.0+-green.svg)](https://www.djangoproject.com/)
[![Tests](https://img.shields.io/badge/tests-201%20passed-success.svg)](tests/)
[![License](https://img.shields.io/badge/license-LGPL%203.0-blue.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## Features

- 🔐 **JWT Authentication** - RS256 with JWKS caching
- 📝 **Structured Logging** - JSON logs with automatic request tracking
- 🔍 **Audit System** - Change tracking with S3 export
- ⚙️ **Celery Integration** - Pre-configured task processing
- 🛠️ **Django Mixins** - UUID, timestamps, user tracking
- ⚡ **Custom Exceptions** - Standardized API errors
- 🎨 **Context Processors** - Site name and domain for templates
- 💱 **Currency Module** - Multi-source exchange rates (BCC/OXR)
- 📄 **PDF Generation** - WeasyPrint integration for Django
- 🏢 **Multi-Tenant** - PostgreSQL schema-based isolation
- 🔑 **Permissions** — Domain-oriented RBAC with named actions, AND/OR logic, groups & grants, translatable labels

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

### Core Modules
- **[Settings](docs/settings.md)** - Configuration reference
- **[JWT](docs/jwt.md)** - Authentication
- **[Audit](docs/audit.md)** - Change tracking
- **[Logging](docs/logger.md)** - Structured logs
- **[Mixins](docs/mixins.md)** - Model/service mixins
- **[Celery](docs/celery.md)** - Task processing

### Additional Modules
- **[Currency](docs/currency.md)** - Exchange rates management
- **[PDF](docs/pdf.md)** - PDF generation with WeasyPrint
- **[Oxiliere](docs/oxiliere.md)** - Multi-tenant architecture
- **[Permissions](docs/permissions.md)** - RBAC with named actions

## Requirements

- Python 3.12+
- Django 5.0+
- PostgreSQL (recommended)

## Development

```bash
git clone https://github.com/oxiliere/oxutils.git
cd oxutils
uv sync
uv run pytest  # 201 tests passing, 4 skipped
```

### Creating Migrations

To generate Django migrations for the audit module:

```bash
make migrations
# or
uv run make_migrations.py
```

See [MIGRATIONS.md](MIGRATIONS.md) for detailed documentation.

## Optional Dependencies

```bash
# Multi-tenant support
uv add oxutils[oxiliere]

# PDF generation
uv add oxutils[pdf]

# Development tools
uv add oxutils[dev]
```

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

### Currency Exchange Rates

```python
from oxutils.currency.models import CurrencyState

# Sync rates from BCC (with OXR fallback)
state = CurrencyState.sync()

# Get latest rates
latest = CurrencyState.objects.latest()
usd_rate = latest.currencies.get(code='USD').rate
eur_rate = latest.currencies.get(code='EUR').rate
```

### PDF Generation

```python
from oxutils.pdf.printer import Printer
from oxutils.pdf.views import WeasyTemplateView

# Standalone PDF generation
printer = Printer(
    template_name='invoice.html',
    context={'invoice': invoice},
    stylesheets=['css/invoice.css']
)
pdf_bytes = printer.write_pdf()

# Class-based view
class InvoicePDFView(WeasyTemplateView):
    template_name = 'invoice.html'
    pdf_filename = 'invoice.pdf'
    pdf_stylesheets = ['css/invoice.css']
```

# Multi-Tenant Setup

```python
# settings.py
TENANT_MODEL = "oxiliere.Tenant"
MIDDLEWARE = [
    'oxutils.oxiliere.middleware.TenantMainMiddleware',
    # ...
]
```

### Permissions (v0.5.0)

```python
# settings.py — define named actions & scopes with translatable labels
from django.utils.translation import gettext_lazy as _

PERMISSION_PRESET = {
    "actions": {
        "orders": {
            "create":  {"implies": [],          "label": _("Create")},
            "approve": {"implies": ["create"],  "label": _("Approve")},
            "cancel":  {"implies": [],          "label": _("Cancel")},
        },
        "articles": {
            "read":    {"implies": [],          "label": _("Read")},
            "write":   {"implies": ["read"],    "label": _("Write")},
            "publish": {"implies": ["write"],   "label": _("Publish")},
        },
    },
    "roles": [{"name": "Editor", "slug": "editor"}],
    "groups": [],
    "role_grants": [
        {"role": "editor", "scope": "articles", "actions": ["write"], "context": {}},
    ],
}

# Scopes — strings or dicts with labels (recommended for frontend i18n)
ACCESS_SCOPES = [
    "articles",
    {"key": "orders", "label": _("Orders")},
]

# Controller — AND (/) and OR (|) operators
from oxutils.permissions.perms import ScopePermission

@api_controller('/orders', permissions=[ScopePermission('orders:create/approve')])
class OrderController:  # user needs create AND approve
    ...

# Frontend endpoint — translated action labels
# GET /api/access/scopes/orders/actions
# → {"scope": "orders", "actions": [
#     {"key": "create",  "label": "Créer"},
#     {"key": "approve", "label": "Approuver"},
#   ]}

# Frontend endpoint — translated scope labels
# GET /api/access/scopes
# → [
#     {"key": "articles", "label": "Articles"},
#     {"key": "orders",   "label": "Commandes"},
#   ]
```

## License

LGPL 3.0 License - see [LICENSE](LICENSE)

## Support

- **Issues**: [GitHub Issues](https://github.com/oxiliere/oxutils/issues)
- **Email**: dev@oxiliere.com

---

**Made with ❤️ by Oxiliere**
