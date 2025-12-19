# Audit System

**Automatic change tracking with S3 export**

## Features

- Automatic model change logging
- Data masking for sensitive fields
- Log export to S3 (ZIP format)
- Configurable retention policies
- Export state tracking with history

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

### Export Logs

```python
from oxutils.audit.export import export_logs_from_date
from datetime import datetime, timedelta

# Export last 7 days
from_date = datetime.now() - timedelta(days=7)
export = export_logs_from_date(from_date=from_date)

print(f"Exported to: {export.data.url}")
print(f"Size: {export.size} bytes")
```

### Log Export Model

```python
from oxutils.audit.models import LogExportState

# Check export status
export = LogExportState.objects.get(id=export_id)

if export.status == ExportStatus.SUCCESS.value:
    # Download URL (presigned, valid 1 hour)
    url = export.data.url
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

- [S3](./s3.md) - Log storage
- [Settings](./settings.md) - Audit configuration
- [Enums](./enums.md) - Export status
