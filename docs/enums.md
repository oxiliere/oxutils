# Enums Documentation

## Overview

OxUtils provides a collection of standardized enumerations (enums) that ensure consistency across the Oxiliere ecosystem. These enums are used throughout models, services, and APIs to represent fixed sets of values with type safety and validation.

All enums inherit from both `str` and `Enum`, making them JSON-serializable and database-friendly while maintaining type safety.

---

## Table of Contents

- [Why String Enums?](#why-string-enums)
- [Available Enums](#available-enums)
  - [InvoiceStatusEnum](#invoicestatusenum)
  - [ExportStatus](#exportstatus)
- [Usage Patterns](#usage-patterns)
  - [In Django Models](#in-django-models)
  - [In API Schemas](#in-api-schemas)
  - [In Service Logic](#in-service-logic)
  - [In Database Queries](#in-database-queries)
- [Best Practices](#best-practices)
- [Creating Custom Enums](#creating-custom-enums)

---

## Why String Enums?

OxUtils enums inherit from both `str` and `Enum` (`class MyEnum(str, Enum)`), providing several advantages:

### Benefits

| Feature | Description |
|---------|-------------|
| **JSON Serialization** | Automatically serializes to string values in JSON responses |
| **Database Storage** | Stores as VARCHAR in database, human-readable in raw SQL |
| **Type Safety** | IDE autocomplete and type checking support |
| **Validation** | Django automatically validates against allowed choices |
| **Readability** | Clear, self-documenting code |
| **Migration Safety** | Adding new values doesn't require database migrations |

### Example

```python
# Without string inheritance
class Status(Enum):
    ACTIVE = "active"

status = Status.ACTIVE
print(status)  # Status.ACTIVE (not JSON serializable)

# With string inheritance (OxUtils pattern)
class Status(str, Enum):
    ACTIVE = "active"

status = Status.ACTIVE
print(status)  # "active" (JSON serializable)
json.dumps({"status": status})  # Works!
```

---

## Available Enums

### InvoiceStatusEnum

Represents the lifecycle states of an invoice.

**Location:** `oxutils.enums.InvoiceStatusEnum`

#### Values

| Value | String | Description |
|-------|--------|-------------|
| `DRAFT` | `"draft"` | Invoice is being prepared and not yet finalized |
| `PENDING` | `"pending"` | Invoice has been sent and awaiting payment |
| `PAID` | `"paid"` | Invoice has been fully paid |
| `OVERDUE` | `"overdue"` | Invoice payment is past due date |
| `CANCELLED` | `"cancelled"` | Invoice has been cancelled and is no longer valid |
| `REFUNDED` | `"refunded"` | Invoice payment has been refunded |

#### State Transitions

```
DRAFT → PENDING → PAID
         ↓         ↓
      OVERDUE   REFUNDED
         ↓
    CANCELLED
```

#### Usage Example

```python
from oxutils.enums import InvoiceStatusEnum
from django.db import models

class Invoice(models.Model):
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in InvoiceStatusEnum],
        default=InvoiceStatusEnum.DRAFT
    )
    
    def mark_as_paid(self):
        """Mark invoice as paid."""
        if self.status != InvoiceStatusEnum.PENDING:
            raise ValueError("Only pending invoices can be marked as paid")
        self.status = InvoiceStatusEnum.PAID
        self.save()
    
    def is_payable(self) -> bool:
        """Check if invoice can be paid."""
        return self.status in [
            InvoiceStatusEnum.PENDING,
            InvoiceStatusEnum.OVERDUE
        ]
```

#### Business Logic Example

```python
class InvoiceService:
    def process_payment(self, invoice_id: str, amount: Decimal):
        invoice = Invoice.objects.get(id=invoice_id)
        
        # Validate status
        if invoice.status == InvoiceStatusEnum.PAID:
            raise ValidationException("Invoice already paid")
        
        if invoice.status == InvoiceStatusEnum.CANCELLED:
            raise ValidationException("Cannot pay cancelled invoice")
        
        if invoice.status == InvoiceStatusEnum.REFUNDED:
            raise ValidationException("Invoice has been refunded")
        
        # Process payment
        if amount >= invoice.total_amount:
            invoice.status = InvoiceStatusEnum.PAID
        
        invoice.save()
        return invoice
```

---

### ExportStatus

Represents the status of audit log export operations.

**Location:** `oxutils.enums.audit.ExportStatus`

#### Values

| Value | String | Description |
|-------|--------|-------------|
| `PENDING` | `"pending"` | Export has been initiated but not yet completed |
| `SUCCESS` | `"success"` | Export completed successfully |
| `FAILED` | `"failed"` | Export failed due to an error |

#### State Transitions

```
PENDING → SUCCESS
   ↓
FAILED
```

#### Usage Example

```python
from oxutils.enums.audit import ExportStatus
from oxutils.audit.models import LogExportState

class LogExportService:
    def create_export(self, from_date, to_date):
        # Create export with pending status
        export = LogExportState.objects.create(
            status=ExportStatus.PENDING,
            from_date=from_date,
            to_date=to_date
        )
        
        try:
            # Perform export
            data = self.export_logs(from_date, to_date)
            export.data = data
            export.status = ExportStatus.SUCCESS
            export.save()
        except Exception as e:
            export.status = ExportStatus.FAILED
            export.error_message = str(e)
            export.save()
            raise
        
        return export
    
    def get_failed_exports(self):
        """Get all failed exports for retry."""
        return LogExportState.objects.filter(
            status=ExportStatus.FAILED
        )
```

#### Monitoring Example

```python
def get_export_statistics():
    """Get export statistics by status."""
    from django.db.models import Count
    
    stats = LogExportState.objects.values('status').annotate(
        count=Count('id')
    )
    
    return {
        'total': LogExportState.objects.count(),
        'pending': LogExportState.objects.filter(
            status=ExportStatus.PENDING
        ).count(),
        'success': LogExportState.objects.filter(
            status=ExportStatus.SUCCESS
        ).count(),
        'failed': LogExportState.objects.filter(
            status=ExportStatus.FAILED
        ).count(),
        'success_rate': calculate_success_rate()
    }
```

---

## Usage Patterns

### In Django Models

#### Basic Usage

```python
from django.db import models
from oxutils.enums import InvoiceStatusEnum

class Invoice(models.Model):
    status = models.CharField(
        max_length=20,
        choices=[(s.value, s.name) for s in InvoiceStatusEnum],
        default=InvoiceStatusEnum.DRAFT
    )
```

#### With Human-Readable Labels

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from oxutils.enums import InvoiceStatusEnum

class Invoice(models.Model):
    status = models.CharField(
        max_length=20,
        choices=[
            (InvoiceStatusEnum.DRAFT, _("Draft")),
            (InvoiceStatusEnum.PENDING, _("Pending Payment")),
            (InvoiceStatusEnum.PAID, _("Paid")),
            (InvoiceStatusEnum.OVERDUE, _("Overdue")),
            (InvoiceStatusEnum.CANCELLED, _("Cancelled")),
            (InvoiceStatusEnum.REFUNDED, _("Refunded")),
        ],
        default=InvoiceStatusEnum.DRAFT
    )
```

#### With Validation

```python
from django.core.exceptions import ValidationError
from oxutils.enums import InvoiceStatusEnum

class Invoice(models.Model):
    status = models.CharField(max_length=20, default=InvoiceStatusEnum.DRAFT)
    
    def clean(self):
        # Validate status transitions
        if self.pk:  # Existing instance
            old_instance = Invoice.objects.get(pk=self.pk)
            if not self._is_valid_transition(old_instance.status, self.status):
                raise ValidationError(
                    f"Invalid status transition from {old_instance.status} to {self.status}"
                )
    
    def _is_valid_transition(self, old_status, new_status):
        valid_transitions = {
            InvoiceStatusEnum.DRAFT: [InvoiceStatusEnum.PENDING, InvoiceStatusEnum.CANCELLED],
            InvoiceStatusEnum.PENDING: [InvoiceStatusEnum.PAID, InvoiceStatusEnum.OVERDUE, InvoiceStatusEnum.CANCELLED],
            InvoiceStatusEnum.OVERDUE: [InvoiceStatusEnum.PAID, InvoiceStatusEnum.CANCELLED],
            InvoiceStatusEnum.PAID: [InvoiceStatusEnum.REFUNDED],
        }
        return new_status in valid_transitions.get(old_status, [])
```

---

### In API Schemas

#### Django Ninja Schema

```python
from ninja import Schema
from oxutils.enums import InvoiceStatusEnum
from typing import Optional

class InvoiceSchema(Schema):
    id: str
    status: InvoiceStatusEnum  # Automatically validated
    amount: float
    
class InvoiceFilterSchema(Schema):
    status: Optional[InvoiceStatusEnum] = None
    min_amount: Optional[float] = None

# API Endpoint
@router.get("/invoices", response=List[InvoiceSchema])
def list_invoices(request, filters: InvoiceFilterSchema = Query(...)):
    queryset = Invoice.objects.all()
    
    if filters.status:
        queryset = queryset.filter(status=filters.status)
    
    return queryset
```

#### Pydantic Schema

```python
from pydantic import BaseModel, Field
from oxutils.enums import InvoiceStatusEnum

class InvoiceCreate(BaseModel):
    customer_id: str
    amount: float = Field(gt=0)
    status: InvoiceStatusEnum = InvoiceStatusEnum.DRAFT

class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatusEnum] = None
    amount: Optional[float] = None
```

---

### In Service Logic

#### Status Checks

```python
from oxutils.enums import InvoiceStatusEnum

class InvoiceService:
    def can_edit(self, invoice: Invoice) -> bool:
        """Check if invoice can be edited."""
        return invoice.status in [
            InvoiceStatusEnum.DRAFT,
            InvoiceStatusEnum.PENDING
        ]
    
    def can_cancel(self, invoice: Invoice) -> bool:
        """Check if invoice can be cancelled."""
        return invoice.status not in [
            InvoiceStatusEnum.PAID,
            InvoiceStatusEnum.REFUNDED,
            InvoiceStatusEnum.CANCELLED
        ]
    
    def requires_payment(self, invoice: Invoice) -> bool:
        """Check if invoice requires payment."""
        return invoice.status in [
            InvoiceStatusEnum.PENDING,
            InvoiceStatusEnum.OVERDUE
        ]
```

#### State Machine Pattern

```python
from oxutils.enums import InvoiceStatusEnum
from typing import Dict, Set

class InvoiceStateMachine:
    TRANSITIONS: Dict[InvoiceStatusEnum, Set[InvoiceStatusEnum]] = {
        InvoiceStatusEnum.DRAFT: {
            InvoiceStatusEnum.PENDING,
            InvoiceStatusEnum.CANCELLED
        },
        InvoiceStatusEnum.PENDING: {
            InvoiceStatusEnum.PAID,
            InvoiceStatusEnum.OVERDUE,
            InvoiceStatusEnum.CANCELLED
        },
        InvoiceStatusEnum.OVERDUE: {
            InvoiceStatusEnum.PAID,
            InvoiceStatusEnum.CANCELLED
        },
        InvoiceStatusEnum.PAID: {
            InvoiceStatusEnum.REFUNDED
        },
        InvoiceStatusEnum.CANCELLED: set(),
        InvoiceStatusEnum.REFUNDED: set(),
    }
    
    @classmethod
    def can_transition(cls, from_status: InvoiceStatusEnum, to_status: InvoiceStatusEnum) -> bool:
        """Check if status transition is valid."""
        return to_status in cls.TRANSITIONS.get(from_status, set())
    
    @classmethod
    def get_allowed_transitions(cls, current_status: InvoiceStatusEnum) -> Set[InvoiceStatusEnum]:
        """Get all allowed transitions from current status."""
        return cls.TRANSITIONS.get(current_status, set())
```

---

### In Database Queries

#### Filtering

```python
from oxutils.enums import InvoiceStatusEnum

# Get all unpaid invoices
unpaid_invoices = Invoice.objects.filter(
    status__in=[InvoiceStatusEnum.PENDING, InvoiceStatusEnum.OVERDUE]
)

# Get all finalized invoices
finalized_invoices = Invoice.objects.filter(
    status__in=[
        InvoiceStatusEnum.PAID,
        InvoiceStatusEnum.CANCELLED,
        InvoiceStatusEnum.REFUNDED
    ]
)

# Exclude draft invoices
active_invoices = Invoice.objects.exclude(status=InvoiceStatusEnum.DRAFT)
```

#### Aggregation

```python
from django.db.models import Count, Sum
from oxutils.enums import InvoiceStatusEnum

# Count invoices by status
status_counts = Invoice.objects.values('status').annotate(
    count=Count('id')
)

# Calculate revenue by status
revenue_by_status = Invoice.objects.values('status').annotate(
    total=Sum('amount')
)

# Get paid invoices total
paid_total = Invoice.objects.filter(
    status=InvoiceStatusEnum.PAID
).aggregate(total=Sum('amount'))['total']
```

#### Conditional Updates

```python
from django.utils import timezone
from oxutils.enums import InvoiceStatusEnum

# Mark overdue invoices
Invoice.objects.filter(
    status=InvoiceStatusEnum.PENDING,
    due_date__lt=timezone.now()
).update(status=InvoiceStatusEnum.OVERDUE)
```

---

## Best Practices

### 1. Always Use Enum Values

**❌ Bad:**
```python
invoice.status = "paid"  # String literal
```

**✅ Good:**
```python
from oxutils.enums import InvoiceStatusEnum
invoice.status = InvoiceStatusEnum.PAID
```

### 2. Use Enum in Comparisons

**❌ Bad:**
```python
if invoice.status == "pending":
    process_payment()
```

**✅ Good:**
```python
from oxutils.enums import InvoiceStatusEnum
if invoice.status == InvoiceStatusEnum.PENDING:
    process_payment()
```

### 3. Leverage Type Hints

```python
from oxutils.enums import InvoiceStatusEnum

def process_invoice(status: InvoiceStatusEnum) -> bool:
    """Process invoice based on status."""
    if status == InvoiceStatusEnum.PAID:
        return True
    return False
```

### 4. Use Enums in Collections

```python
from oxutils.enums import InvoiceStatusEnum

PAYABLE_STATUSES = {
    InvoiceStatusEnum.PENDING,
    InvoiceStatusEnum.OVERDUE
}

FINAL_STATUSES = {
    InvoiceStatusEnum.PAID,
    InvoiceStatusEnum.CANCELLED,
    InvoiceStatusEnum.REFUNDED
}

def is_payable(invoice: Invoice) -> bool:
    return invoice.status in PAYABLE_STATUSES
```

### 5. Document Status Meanings

```python
from oxutils.enums import InvoiceStatusEnum

class Invoice(models.Model):
    """
    Invoice model.
    
    Status Flow:
        DRAFT → PENDING → PAID
                  ↓         ↓
               OVERDUE   REFUNDED
                  ↓
              CANCELLED
    
    Status Descriptions:
        - DRAFT: Invoice is being prepared
        - PENDING: Sent to customer, awaiting payment
        - PAID: Payment received and confirmed
        - OVERDUE: Payment deadline passed
        - CANCELLED: Invoice voided
        - REFUNDED: Payment returned to customer
    """
    status = models.CharField(
        max_length=20,
        choices=[(s.value, s.name) for s in InvoiceStatusEnum],
        default=InvoiceStatusEnum.DRAFT
    )
```

### 6. Validate Transitions

```python
from oxutils.enums import InvoiceStatusEnum
from oxutils.exceptions import ValidationException

class InvoiceService:
    VALID_TRANSITIONS = {
        InvoiceStatusEnum.DRAFT: [InvoiceStatusEnum.PENDING],
        InvoiceStatusEnum.PENDING: [InvoiceStatusEnum.PAID, InvoiceStatusEnum.OVERDUE],
        # ... more transitions
    }
    
    def update_status(self, invoice: Invoice, new_status: InvoiceStatusEnum):
        """Update invoice status with validation."""
        valid_next_statuses = self.VALID_TRANSITIONS.get(invoice.status, [])
        
        if new_status not in valid_next_statuses:
            raise ValidationException(
                f"Cannot transition from {invoice.status} to {new_status}"
            )
        
        invoice.status = new_status
        invoice.save()
```

---

## Creating Custom Enums

### Basic Pattern

```python
from enum import Enum

class OrderStatus(str, Enum):
    """Order lifecycle status."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
```

### With Helper Methods

```python
from enum import Enum
from typing import Set

class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"
    
    @classmethod
    def get_active_statuses(cls) -> Set['PaymentStatus']:
        """Get statuses that represent active payments."""
        return {cls.PENDING, cls.AUTHORIZED, cls.CAPTURED}
    
    @classmethod
    def get_final_statuses(cls) -> Set['PaymentStatus']:
        """Get statuses that represent finalized payments."""
        return {cls.CAPTURED, cls.FAILED, cls.REFUNDED}
    
    def is_active(self) -> bool:
        """Check if this status represents an active payment."""
        return self in self.get_active_statuses()
    
    def is_final(self) -> bool:
        """Check if this status is final."""
        return self in self.get_final_statuses()
```

### With Metadata

```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict

@dataclass
class StatusMetadata:
    label: str
    description: str
    color: str

class SubscriptionStatus(str, Enum):
    """Subscription status with metadata."""
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    
    @property
    def metadata(self) -> StatusMetadata:
        """Get metadata for this status."""
        return self._metadata()[self]
    
    @classmethod
    def _metadata(cls) -> Dict['SubscriptionStatus', StatusMetadata]:
        return {
            cls.TRIAL: StatusMetadata(
                label="Trial Period",
                description="User is in trial period",
                color="#FFA500"
            ),
            cls.ACTIVE: StatusMetadata(
                label="Active",
                description="Subscription is active and paid",
                color="#00FF00"
            ),
            cls.PAST_DUE: StatusMetadata(
                label="Past Due",
                description="Payment failed, grace period active",
                color="#FF0000"
            ),
            cls.CANCELLED: StatusMetadata(
                label="Cancelled",
                description="User cancelled subscription",
                color="#808080"
            ),
            cls.EXPIRED: StatusMetadata(
                label="Expired",
                description="Subscription expired",
                color="#000000"
            ),
        }

# Usage
status = SubscriptionStatus.ACTIVE
print(status.metadata.label)  # "Active"
print(status.metadata.color)  # "#00FF00"
```

---

## Testing Enums

### Unit Tests

```python
import pytest
from oxutils.enums import InvoiceStatusEnum

class TestInvoiceStatusEnum:
    def test_enum_values(self):
        """Test enum has expected values."""
        assert InvoiceStatusEnum.DRAFT == "draft"
        assert InvoiceStatusEnum.PAID == "paid"
    
    def test_enum_membership(self):
        """Test enum membership checks."""
        assert InvoiceStatusEnum.PENDING in InvoiceStatusEnum
        assert "invalid" not in [s.value for s in InvoiceStatusEnum]
    
    def test_enum_iteration(self):
        """Test enum can be iterated."""
        statuses = list(InvoiceStatusEnum)
        assert len(statuses) == 6
        assert InvoiceStatusEnum.DRAFT in statuses
    
    def test_enum_comparison(self):
        """Test enum comparisons."""
        status1 = InvoiceStatusEnum.PAID
        status2 = InvoiceStatusEnum.PAID
        assert status1 == status2
        assert status1 == "paid"  # String comparison works
```

### Integration Tests

```python
import pytest
from django.test import TestCase
from oxutils.enums import InvoiceStatusEnum

class TestInvoiceModel(TestCase):
    def test_create_invoice_with_enum(self):
        """Test creating invoice with enum status."""
        invoice = Invoice.objects.create(
            amount=100.00,
            status=InvoiceStatusEnum.DRAFT
        )
        assert invoice.status == InvoiceStatusEnum.DRAFT
    
    def test_filter_by_enum(self):
        """Test filtering invoices by enum status."""
        Invoice.objects.create(amount=100, status=InvoiceStatusEnum.PAID)
        Invoice.objects.create(amount=200, status=InvoiceStatusEnum.PENDING)
        
        paid = Invoice.objects.filter(status=InvoiceStatusEnum.PAID)
        assert paid.count() == 1
    
    def test_enum_validation(self):
        """Test invalid enum values are rejected."""
        with pytest.raises(ValueError):
            Invoice.objects.create(
                amount=100,
                status="invalid_status"
            )
```

---

## Common Patterns

### Status Groups

```python
from oxutils.enums import InvoiceStatusEnum

# Define status groups
DRAFT_STATUSES = {InvoiceStatusEnum.DRAFT}
ACTIVE_STATUSES = {InvoiceStatusEnum.PENDING, InvoiceStatusEnum.OVERDUE}
COMPLETED_STATUSES = {InvoiceStatusEnum.PAID, InvoiceStatusEnum.REFUNDED}
CANCELLED_STATUSES = {InvoiceStatusEnum.CANCELLED}

def get_status_group(status: InvoiceStatusEnum) -> str:
    """Get the group name for a status."""
    if status in DRAFT_STATUSES:
        return "draft"
    elif status in ACTIVE_STATUSES:
        return "active"
    elif status in COMPLETED_STATUSES:
        return "completed"
    elif status in CANCELLED_STATUSES:
        return "cancelled"
    return "unknown"
```

### Status Progression

```python
from oxutils.enums import InvoiceStatusEnum

STATUS_PROGRESSION = [
    InvoiceStatusEnum.DRAFT,
    InvoiceStatusEnum.PENDING,
    InvoiceStatusEnum.PAID,
]

def get_next_status(current: InvoiceStatusEnum) -> InvoiceStatusEnum | None:
    """Get the next status in progression."""
    try:
        current_index = STATUS_PROGRESSION.index(current)
        return STATUS_PROGRESSION[current_index + 1]
    except (ValueError, IndexError):
        return None
```

---

## Migration Guide

### Adding New Enum Values

When adding new values to existing enums:

1. **Add the value to the enum:**
```python
class InvoiceStatusEnum(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"  # New value
```

2. **Update model choices (if using explicit choices):**
```python
# No database migration needed for CharField!
# Just deploy the code change
```

3. **Update business logic:**
```python
def is_payable(invoice: Invoice) -> bool:
    return invoice.status in [
        InvoiceStatusEnum.PENDING,
        InvoiceStatusEnum.OVERDUE,
        InvoiceStatusEnum.PARTIALLY_PAID,  # Include new status
    ]
```

---

## Related Documentation

- [Mixins](./mixins.md) - Model and service mixins using enums
- [Audit System](./audit.md) - ExportStatus enum usage
- [Settings & Configuration](./settings.md) - Configuration management

---

## Support

For questions or issues regarding enums, please contact the Oxiliere development team or open an issue in the repository.
