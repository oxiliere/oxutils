# Audit System

**Automatic change tracking**

## Features

- Automatic model change logging
- Data masking for sensitive fields
- Configurable retention policies

## Setup

The audit module is automatically included when you use `UTILS_APPS`:

```python
# settings.py
from oxutils.conf import UTILS_APPS, AUDIT_MIDDLEWARE

INSTALLED_APPS = [
    *UTILS_APPS,  # Includes 'oxutils.audit'
    # your apps...
]

MIDDLEWARE = [
    # django middleware....
    *AUDIT_MIDDLEWARE,
    # your middleware...
]
```

Then run migrations:

```bash
python manage.py migrate audit
```

## Configuration

```bash
OXI_LOG_ACCESS=True          # Enable read operation logging
OXI_RETENTION_DELAY=30       # Days to retain logs
```

## Usage

### Enable Auditing

```python
# models.py
from auditlog.registry import auditlog

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

# Register for auditing
auditlog.register(Product)
```

### Mask Sensitive Fields

```python
auditlog.register(
    User,
    mask_fields=['password', 'ssn']
)
```

## Automatic Cleanup

Configure retention in settings:

```python
OXI_RETENTION_DELAY=90  # Keep logs for 90 days
```

## Log Structure

Each change is logged with:
- User who made the change
- Timestamp
- Changed fields (before/after)
- Action type (create, update, delete)
- Request ID (correlation with application logs)

## Request ID Correlation

Audit logs automatically include the `request_id` from django-structlog in the `cid` field, allowing you to correlate audit entries with application logs:

```python
from auditlog.models import LogEntry

# Find all audit entries for a specific request
request_id = "abc-def-123-456"
entries = LogEntry.objects.filter(cid=request_id)

# See what was changed in this request
for entry in entries:
    print(f"{entry.action}: {entry.object_repr}")
    print(f"Changes: {entry.changes}")
```

This enables full request tracing across both application logs and audit logs.

## Related Docs

- [Settings](./settings.md) - Audit configuration
- [Enums](./enums.md) - Export status
