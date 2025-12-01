# Audit System Documentation

## Overview

The OxUtils Audit System provides comprehensive audit logging capabilities for Django applications in the Oxiliere ecosystem. Built on top of `django-auditlog`, it offers automatic change tracking, data masking for sensitive fields, and efficient log export functionality with S3 integration.

### Key Features

- **Automatic Change Tracking**: Tracks all model changes (create, update, delete)
- **User Attribution**: Records which user performed each action
- **Data Masking**: Automatically masks sensitive fields (passwords, tokens, credit cards, etc.)
- **Log Export**: Export audit logs to compressed ZIP files
- **S3 Integration**: Store exports in S3 for long-term archival
- **Access Logging**: Optional logging of object access (read operations)
- **Retention Management**: Configurable retention policies

---

## Table of Contents

- [Installation & Configuration](#installation--configuration)
- [Models](#models)
  - [LogExportState](#logexportstate)
  - [LogExportHistory](#logexporthistory)
- [Export Utilities](#export-utilities)
  - [export_logs_from_date](#export_logs_from_date)
  - [export_logs_since_last_export](#export_logs_since_last_export)
  - [get_export_statistics](#get_export_statistics)
- [Data Masking](#data-masking)
- [Configuration Settings](#configuration-settings)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)
- [Monitoring & Maintenance](#monitoring--maintenance)

---

## Installation & Configuration

### Basic Setup

1. **Add to INSTALLED_APPS:**

```python
INSTALLED_APPS = [
    # ...
    'auditlog',
    'oxutils.audit',
    # ...
]
```

2. **Configure Settings:**

```python
from oxutils.audit.settings import *

# Enable access logging (optional)
OXI_LOG_ACCESS = True

# Set retention delay (days)
OXI_RETENTION_DELAY = 7

# Configure S3 for log storage
OXI_USE_LOG_S3 = True
OXI_LOG_S3_ACCESS_KEY_ID = "your-access-key"
OXI_LOG_S3_SECRET_ACCESS_KEY = "your-secret-key"
OXI_LOG_S3_STORAGE_BUCKET_NAME = "your-bucket-name"
OXI_LOG_S3_LOCATION = "audit_logs"
```

3. **Register Models for Auditing:**

```python
from auditlog.registry import auditlog
from myapp.models import User, Order, Payment

# Register models to track
auditlog.register(User)
auditlog.register(Order)
auditlog.register(Payment)
```

### Advanced Configuration

```python
# Disable remote address tracking
AUDITLOG_DISABLE_REMOTE_ADDR = False

# Fields to mask in audit logs
AUDITLOG_MASK_TRACKING_FIELDS = (
    "password",
    "api_key",
    "secret_token",
    "token",
    "credit_card",
    "ssn",
)

# Fields to exclude from tracking
AUDITLOG_EXCLUDE_TRACKING_FIELDS = (
    "created_at",
    "updated_at",
    "last_login",
)

# Correlation ID settings
CID_GENERATE = False
AUDITLOG_CID_GETTER = "cid.locals.get_cid"
```

---

## Models

### LogExportState

Represents the state of an audit log export operation.

**Location:** `oxutils.audit.models.LogExportState`

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `AutoField` | Primary key |
| `last_export_date` | `DateTimeField` | Date of the last successful export |
| `status` | `CharField` | Export status (pending, success, failed) |
| `data` | `FileField` | ZIP file containing exported logs (stored in S3) |
| `size` | `BigIntegerField` | Size of the export file in bytes |
| `created_at` | `DateTimeField` | When the export was created |
| `updated_at` | `DateTimeField` | When the export was last updated |

#### Methods

##### `create(size: int = 0) -> LogExportState`

Class method to create a new export state with pending status.

```python
export = LogExportState.create(size=0)
```

##### `set_success() -> None`

Mark the export as successful and create a history entry.

```python
export.set_success()
```

**Behavior:**
- Sets status to `SUCCESS`
- Updates `last_export_date` to current time
- Creates a `LogExportHistory` entry
- Updates the record atomically

##### `set_failed() -> None`

Mark the export as failed and create a history entry.

```python
export.set_failed()
```

**Behavior:**
- Sets status to `FAILED`
- Creates a `LogExportHistory` entry
- Updates the record atomically

#### Usage Example

```python
from oxutils.audit.models import LogExportState
from oxutils.enums.audit import ExportStatus

# Create a new export
export = LogExportState.create()

try:
    # Perform export operations
    export.data.save('logs.zip', content)
    export.size = len(content)
    export.set_success()
except Exception as e:
    export.set_failed()
    raise

# Query exports
successful_exports = LogExportState.objects.filter(
    status=ExportStatus.SUCCESS
)

failed_exports = LogExportState.objects.filter(
    status=ExportStatus.FAILED
)
```

---

### LogExportHistory

Tracks the history of export status changes.

**Location:** `oxutils.audit.models.LogExportHistory`

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `AutoField` | Primary key |
| `state` | `ForeignKey` | Reference to LogExportState |
| `status` | `CharField` | Status at this point in history |
| `created_at` | `DateTimeField` | When this history entry was created |

#### Usage Example

```python
from oxutils.audit.models import LogExportHistory

# Get history for an export
export = LogExportState.objects.get(id=export_id)
history = export.log_histories.all().order_by('-created_at')

for entry in history:
    print(f"{entry.created_at}: {entry.status}")
```

---

## Export Utilities

### export_logs_from_date

Export audit logs from a specific date range to a compressed ZIP file.

**Location:** `oxutils.audit.export.export_logs_from_date`

#### Signature

```python
def export_logs_from_date(
    from_date: datetime,
    to_date: Optional[datetime] = None,
    batch_size: int = 5000
) -> LogExportState
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from_date` | `datetime` | Required | Start date for export (inclusive) |
| `to_date` | `datetime` | `None` | End date for export (inclusive). If None, uses current time |
| `batch_size` | `int` | `5000` | Number of records to process per batch |

#### Returns

`LogExportState` - The created export state with compressed data

#### Raises

`Exception` - If export fails, the LogExportState status will be set to FAILED

#### Features

- **Optimized for S3**: Streaming processing with minimal memory usage
- **Batch Processing**: Processes logs in configurable batches
- **Compression**: ZIP compression with optimal settings (level 6)
- **Metadata**: Includes export metadata (date range, record count, etc.)
- **Atomic Operations**: Uses database transactions for consistency

#### Export Format

The exported ZIP file contains:

```
audit_logs_20241201_20241207.zip
├── metadata.json          # Export metadata
├── logs_batch_0001.json   # First batch of logs
├── logs_batch_0002.json   # Second batch of logs
└── ...
```

**metadata.json structure:**
```json
{
  "export_date": "2024-12-01T15:30:00Z",
  "from_date": "2024-12-01T00:00:00Z",
  "to_date": "2024-12-07T23:59:59Z",
  "total_records": 15000,
  "batch_size": 5000,
  "total_batches": 3
}
```

**Log entry structure:**
```json
{
  "id": 12345,
  "timestamp": "2024-12-01T10:30:00Z",
  "action": "UPDATE",
  "content_type": {
    "app_label": "myapp",
    "model": "user"
  },
  "object_pk": "550e8400-e29b-41d4-a716-446655440000",
  "object_repr": "john@example.com",
  "changes": {
    "email": ["old@example.com", "new@example.com"],
    "updated_at": ["2024-12-01T10:00:00Z", "2024-12-01T10:30:00Z"]
  },
  "actor": {
    "id": 1,
    "username": "admin"
  },
  "remote_addr": "192.168.1.1",
  "additional_data": {}
}
```

#### Usage Example

```python
from datetime import datetime, timedelta
from oxutils.audit.export import export_logs_from_date

# Export last 7 days
from_date = datetime.now() - timedelta(days=7)
export = export_logs_from_date(from_date=from_date)

print(f"Export ID: {export.id}")
print(f"Status: {export.status}")
print(f"Size: {export.size / (1024 * 1024):.2f} MB")
print(f"File: {export.data.url}")

# Export specific date range
from_date = datetime(2024, 12, 1)
to_date = datetime(2024, 12, 7)
export = export_logs_from_date(
    from_date=from_date,
    to_date=to_date,
    batch_size=10000  # Larger batches for better performance
)
```

#### Performance Characteristics

| Dataset Size | Memory Usage | Processing Time | File Size (approx) |
|--------------|--------------|-----------------|-------------------|
| 10,000 logs | ~50 MB | ~5 seconds | ~2 MB |
| 100,000 logs | ~50 MB | ~30 seconds | ~15 MB |
| 1,000,000 logs | ~50 MB | ~5 minutes | ~120 MB |

*Note: Memory usage remains constant due to streaming processing*

---

### export_logs_since_last_export

Export logs since the last successful export (incremental export).

**Location:** `oxutils.audit.export.export_logs_since_last_export`

#### Signature

```python
def export_logs_since_last_export(
    batch_size: int = 5000
) -> Optional[LogExportState]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `batch_size` | `int` | `5000` | Number of records to process per batch |

#### Returns

`Optional[LogExportState]` - The created export state, or None if no logs to export

#### Usage Example

```python
from oxutils.audit.export import export_logs_since_last_export

# Export new logs since last export
export = export_logs_since_last_export()

if export:
    print(f"Exported {export.size} bytes")
else:
    print("No new logs to export")
```

#### Scheduled Export Example

```python
# In your Celery tasks or cron job
from celery import shared_task
from oxutils.audit.export import export_logs_since_last_export

@shared_task
def daily_log_export():
    """Export audit logs daily."""
    try:
        export = export_logs_since_last_export()
        if export:
            # Notify administrators
            send_notification(
                f"Daily audit log export completed. Size: {export.size} bytes"
            )
    except Exception as e:
        # Handle errors
        send_error_notification(f"Audit log export failed: {str(e)}")
```

---

### get_export_statistics

Get statistics about log exports.

**Location:** `oxutils.audit.export.get_export_statistics`

#### Signature

```python
def get_export_statistics() -> dict
```

#### Returns

Dictionary with the following keys:

| Key | Type | Description |
|-----|------|-------------|
| `total_exports` | `int` | Total number of exports |
| `successful_exports` | `int` | Number of successful exports |
| `failed_exports` | `int` | Number of failed exports |
| `pending_exports` | `int` | Number of pending exports |
| `last_export_date` | `datetime` | Date of last successful export |
| `total_size_bytes` | `int` | Total size of all successful exports in bytes |
| `total_size_mb` | `float` | Total size in megabytes |

#### Usage Example

```python
from oxutils.audit.export import get_export_statistics

stats = get_export_statistics()

print(f"Total exports: {stats['total_exports']}")
print(f"Success rate: {stats['successful_exports'] / stats['total_exports'] * 100:.1f}%")
print(f"Total storage used: {stats['total_size_mb']:.2f} MB")
print(f"Last export: {stats['last_export_date']}")
```

#### Dashboard Example

```python
from django.http import JsonResponse
from oxutils.audit.export import get_export_statistics

def audit_dashboard(request):
    """API endpoint for audit dashboard."""
    stats = get_export_statistics()
    
    return JsonResponse({
        'exports': {
            'total': stats['total_exports'],
            'successful': stats['successful_exports'],
            'failed': stats['failed_exports'],
            'pending': stats['pending_exports'],
            'success_rate': (
                stats['successful_exports'] / stats['total_exports'] * 100
                if stats['total_exports'] > 0 else 0
            )
        },
        'storage': {
            'total_bytes': stats['total_size_bytes'],
            'total_mb': stats['total_size_mb'],
            'total_gb': round(stats['total_size_mb'] / 1024, 2)
        },
        'last_export': stats['last_export_date'].isoformat() if stats['last_export_date'] else None
    })
```

---

## Data Masking

The audit system includes built-in masking functions to protect sensitive data in audit logs.

**Location:** `oxutils.audit.masks`

### Available Mask Functions

#### number_mask

Masks a number showing only the last 4 digits.

```python
from oxutils.audit.masks import number_mask

number_mask("1234567890")  # "****7890"
number_mask("123")         # "***"
```

#### phone_number_mask

Masks a phone number showing only the last 4 digits.

```python
from oxutils.audit.masks import phone_number_mask

phone_number_mask("+1 (555) 123-4567")  # "****4567"
phone_number_mask("555-1234")           # "****1234"
```

#### credit_card_mask

Masks a credit card number showing only the last 4 digits.

```python
from oxutils.audit.masks import credit_card_mask

credit_card_mask("4532 1234 5678 9010")  # "****9010"
credit_card_mask("4532-1234-5678-9010")  # "****9010"
```

#### email_mask

Masks an email address showing only the first character and domain.

```python
from oxutils.audit.masks import email_mask

email_mask("john.doe@example.com")  # "j*******@example.com"
email_mask("a@test.com")            # "a@test.com"
```

### Configuring Field Masking

Configure which fields should be masked in `settings.py`:

```python
AUDITLOG_MASK_TRACKING_FIELDS = (
    "password",
    "api_key",
    "secret_token",
    "token",
    "credit_card",
    "credit_card_number",
    "ssn",
    "social_security_number",
    "phone",
    "phone_number",
)
```

### Custom Mask Functions

Create custom mask functions for your specific needs:

```python
# myapp/masks.py
def custom_mask(value: str) -> str:
    """Custom masking logic."""
    if not value:
        return ""
    # Your masking logic here
    return "***MASKED***"

# Register with auditlog
from auditlog.models import LogEntry
from auditlog import registry

# Apply custom mask to specific model field
registry.register(
    MyModel,
    mask_fields=['sensitive_field'],
    mask_function=custom_mask
)
```

---

## Configuration Settings

### Audit Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `OXI_LOG_ACCESS` | `bool` | `False` | Enable logging of read operations |
| `OXI_RETENTION_DELAY` | `int` | `7` | Number of days to retain logs |

### Auditlog Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `AUDITLOG_DISABLE_REMOTE_ADDR` | `bool` | `False` | Disable IP address tracking |
| `AUDITLOG_MASK_TRACKING_FIELDS` | `tuple` | See above | Fields to mask in logs |
| `AUDITLOG_EXCLUDE_TRACKING_FIELDS` | `tuple` | See above | Fields to exclude from tracking |
| `AUDITLOG_CID_GETTER` | `str` | `"cid.locals.get_cid"` | Correlation ID getter function |
| `AUDITLOG_LOGENTRY_MODEL` | `str` | `"auditlog.LogEntry"` | Custom LogEntry model |

### S3 Storage Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `OXI_USE_LOG_S3` | `bool` | `False` | Enable S3 storage for logs |
| `OXI_LOG_S3_ACCESS_KEY_ID` | `str` | `None` | AWS access key ID |
| `OXI_LOG_S3_SECRET_ACCESS_KEY` | `str` | `None` | AWS secret access key |
| `OXI_LOG_S3_STORAGE_BUCKET_NAME` | `str` | `None` | S3 bucket name |
| `OXI_LOG_S3_DEFAULT_ACL` | `str` | `"private"` | Default ACL for log files |
| `OXI_LOG_S3_LOCATION` | `str` | `"oxi_logs"` | S3 folder path |

---

## Usage Examples

### Basic Model Auditing

```python
# models.py
from django.db import models
from auditlog.registry import auditlog

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()

# Register for auditing
auditlog.register(Product)

# Usage - changes are automatically logged
product = Product.objects.create(name="Widget", price=19.99, stock=100)
# LogEntry created with action=CREATE

product.price = 24.99
product.save()
# LogEntry created with action=UPDATE, changes={"price": [19.99, 24.99]}

product.delete()
# LogEntry created with action=DELETE
```

### Access Logging

```python
from oxutils.mixins.services import BaseService

class ProductService(BaseService):
    def get_product(self, product_id: str):
        """Get product with access logging."""
        product = Product.objects.get(id=product_id)
        
        # Log access if enabled
        self.object_accessed(Product, product)
        
        return product
```

### Manual Export

```python
from datetime import datetime, timedelta
from oxutils.audit.export import export_logs_from_date

def export_monthly_logs(year: int, month: int):
    """Export logs for a specific month."""
    from_date = datetime(year, month, 1)
    
    # Calculate last day of month
    if month == 12:
        to_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        to_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
    
    export = export_logs_from_date(
        from_date=from_date,
        to_date=to_date,
        batch_size=10000
    )
    
    return export
```

### Automated Cleanup

```python
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from auditlog.models import LogEntry
from oxutils.settings import oxi_settings

@shared_task
def cleanup_old_logs():
    """Delete logs older than retention period."""
    retention_days = oxi_settings.retention_delay
    cutoff_date = timezone.now() - timedelta(days=retention_days)
    
    # Export before deletion
    export = export_logs_from_date(
        from_date=cutoff_date - timedelta(days=retention_days),
        to_date=cutoff_date
    )
    
    if export.status == 'success':
        # Delete old logs
        deleted_count = LogEntry.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()[0]
        
        return f"Deleted {deleted_count} logs older than {retention_days} days"
```

### Query Audit Logs

```python
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType

# Get all changes for a specific object
product = Product.objects.get(id=product_id)
content_type = ContentType.objects.get_for_model(Product)
logs = LogEntry.objects.filter(
    content_type=content_type,
    object_pk=str(product.pk)
).order_by('-timestamp')

# Get changes by a specific user
user_logs = LogEntry.objects.filter(
    actor=user
).order_by('-timestamp')

# Get changes in a date range
from datetime import datetime, timedelta
recent_logs = LogEntry.objects.filter(
    timestamp__gte=datetime.now() - timedelta(days=7)
)

# Get specific action types
creates = LogEntry.objects.filter(action=LogEntry.Action.CREATE)
updates = LogEntry.objects.filter(action=LogEntry.Action.UPDATE)
deletes = LogEntry.objects.filter(action=LogEntry.Action.DELETE)
```

---

## Best Practices

### 1. Register Models Selectively

Only register models that require auditing to minimize database overhead.

```python
# ✅ Good - Only audit critical models
auditlog.register(User)
auditlog.register(Payment)
auditlog.register(Order)

# ❌ Bad - Don't audit everything
auditlog.register(LogEntry)  # Never audit the audit log itself!
auditlog.register(Session)   # High volume, low value
```

### 2. Configure Field Exclusions

Exclude fields that change frequently but aren't important for auditing.

```python
AUDITLOG_EXCLUDE_TRACKING_FIELDS = (
    "created_at",
    "updated_at",
    "last_login",
    "view_count",
    "cache_key",
)
```

### 3. Use Regular Exports

Export and archive logs regularly to manage database size.

```python
# Daily export via Celery
@shared_task
def daily_audit_export():
    export_logs_since_last_export()

# Schedule in Celery Beat
CELERY_BEAT_SCHEDULE = {
    'daily-audit-export': {
        'task': 'myapp.tasks.daily_audit_export',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}
```

### 4. Monitor Export Health

Set up monitoring for export failures.

```python
from oxutils.audit.export import get_export_statistics

def check_export_health():
    """Check if exports are running successfully."""
    stats = get_export_statistics()
    
    # Alert if no exports in last 48 hours
    if stats['last_export_date']:
        hours_since_export = (
            timezone.now() - stats['last_export_date']
        ).total_seconds() / 3600
        
        if hours_since_export > 48:
            send_alert("No audit exports in 48 hours!")
    
    # Alert if high failure rate
    if stats['total_exports'] > 0:
        failure_rate = stats['failed_exports'] / stats['total_exports']
        if failure_rate > 0.1:  # 10% failure rate
            send_alert(f"High export failure rate: {failure_rate:.1%}")
```

### 5. Secure Sensitive Data

Always mask sensitive fields and use private S3 storage.

```python
# Configure masking
AUDITLOG_MASK_TRACKING_FIELDS = (
    "password",
    "api_key",
    "secret_token",
    "credit_card",
    "ssn",
)

# Use private S3 storage
OXI_USE_LOG_S3 = True
OXI_LOG_S3_DEFAULT_ACL = "private"
```

### 6. Implement Retention Policies

Define and enforce data retention policies.

```python
# settings.py
OXI_RETENTION_DELAY = 90  # 90 days

# Automated cleanup
@shared_task
def enforce_retention_policy():
    """Enforce audit log retention policy."""
    cutoff_date = timezone.now() - timedelta(
        days=oxi_settings.retention_delay
    )
    
    # Export before deletion
    export = export_logs_from_date(
        from_date=cutoff_date - timedelta(days=7),
        to_date=cutoff_date
    )
    
    if export.status == 'success':
        LogEntry.objects.filter(timestamp__lt=cutoff_date).delete()
```

---

## Monitoring & Maintenance

### Health Check Endpoint

```python
from django.http import JsonResponse
from oxutils.audit.export import get_export_statistics
from auditlog.models import LogEntry

def audit_health_check(request):
    """Health check endpoint for audit system."""
    stats = get_export_statistics()
    
    # Check log count
    log_count = LogEntry.objects.count()
    
    # Check last export
    hours_since_export = None
    if stats['last_export_date']:
        hours_since_export = (
            timezone.now() - stats['last_export_date']
        ).total_seconds() / 3600
    
    # Determine health status
    status = "healthy"
    issues = []
    
    if hours_since_export and hours_since_export > 48:
        status = "warning"
        issues.append("No exports in 48 hours")
    
    if stats['failed_exports'] > stats['successful_exports'] * 0.1:
        status = "warning"
        issues.append("High failure rate")
    
    if log_count > 1000000:
        status = "warning"
        issues.append("High log count - consider cleanup")
    
    return JsonResponse({
        'status': status,
        'issues': issues,
        'metrics': {
            'log_count': log_count,
            'hours_since_export': hours_since_export,
            'export_stats': stats
        }
    })
```

### Monitoring Metrics

Key metrics to monitor:

1. **Export Success Rate**: Should be > 95%
2. **Time Since Last Export**: Should be < 24 hours
3. **Log Growth Rate**: Track daily log volume
4. **Storage Usage**: Monitor S3 storage costs
5. **Export Duration**: Track export performance

---

## Troubleshooting

### Common Issues

#### Export Fails with Memory Error

**Solution:** Reduce batch size

```python
export = export_logs_from_date(
    from_date=from_date,
    batch_size=1000  # Reduce from default 5000
)
```

#### S3 Upload Fails

**Solution:** Check S3 credentials and permissions

```python
# Verify settings
print(oxi_settings.log_s3_access_key_id)
print(oxi_settings.log_s3_storage_bucket_name)

# Test S3 connection
from oxutils.s3.storages import LogStorage
storage = LogStorage()
storage.bucket.objects.all()  # Should not raise error
```

#### Logs Not Being Created

**Solution:** Verify model registration

```python
from auditlog.registry import auditlog

# Check if model is registered
print(auditlog.get_models())  # Should include your model
```

---

## Related Documentation

- [Enums](./enums.md) - ExportStatus enum
- [Mixins](./mixins.md) - TimestampMixin and model mixins
- [S3 Storage](./s3.md) - LogStorage for exports
- [Celery Integration](./celery.md) - Async log export tasks
- [Settings & Configuration](./settings.md) - Audit configuration

---

## Support

For questions or issues regarding the audit system, please contact the Oxiliere development team or open an issue in the repository.
