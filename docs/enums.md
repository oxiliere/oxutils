# Enums

**Standardized enumerations for the Oxiliere ecosystem**

## Available Enums

### ExportStatus

```python
from oxutils.enums.audit import ExportStatus

class LogExportState(models.Model):
    status = models.CharField(
        max_length=20,
        choices=[(s.value, s.value) for s in ExportStatus],
        default=ExportStatus.PENDING.value
    )

# Values
ExportStatus.PENDING   # 'pending'
ExportStatus.SUCCESS   # 'success'
ExportStatus.FAILED    # 'failed'
```

### InvoiceStatusEnum

```python
from oxutils.enums import InvoiceStatusEnum

# Available in oxutils.enums module
```

## Usage

```python
# In models
status = models.CharField(
    max_length=20,
    choices=[(s.value, s.value) for s in ExportStatus]
)

# In code
if export.status == ExportStatus.SUCCESS.value:
    print("Export completed")

# Iteration
for status in ExportStatus:
    print(status.value)
```

## Related Docs

- [Audit](./audit.md) - Export status usage
