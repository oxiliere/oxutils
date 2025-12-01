# Mixins Documentation

## Overview

OxUtils provides a comprehensive set of mixins to enhance Django models, services, schemas, and exception handling. These mixins follow Django best practices and promote code reusability across the Oxiliere ecosystem.

---

## Table of Contents

- [Model Mixins](#model-mixins)
  - [UUIDPrimaryKeyMixin](#uuidprimarykeymixin)
  - [TimestampMixin](#timestampmixin)
  - [UserTrackingMixin](#usertrackingmixin)
  - [SlugMixin](#slugmixin)
  - [NameMixin](#namemixin)
  - [ActiveMixin](#activemixin)
  - [OrderingMixin](#orderingmixin)
  - [BaseModelMixin](#basemodelmixin)
- [Service Mixins](#service-mixins)
  - [BaseService](#baseservice)
- [Schema Mixins](#schema-mixins)
  - [ResponseSchema](#responseschema)
- [Exception Mixins](#exception-mixins)
  - [DetailDictMixin](#detaildictmixin)

---

## Model Mixins

Model mixins are abstract Django model classes that provide common fields and functionality. They are located in `oxutils.models.base`.

### UUIDPrimaryKeyMixin

Provides a UUID-based primary key instead of the default auto-incrementing integer.

**Location:** `oxutils.models.base.UUIDPrimaryKeyMixin`

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUIDField` | UUID primary key, automatically generated using `uuid.uuid4()` |

#### Usage

```python
from django.db import models
from oxutils.models.base import UUIDPrimaryKeyMixin

class Product(UUIDPrimaryKeyMixin):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
```

#### Benefits

- **Security**: UUIDs are non-sequential, preventing enumeration attacks
- **Distributed systems**: Safe for use across multiple databases
- **Uniqueness**: Globally unique identifiers

---

### TimestampMixin

Automatically tracks creation and modification timestamps.

**Location:** `oxutils.models.base.TimestampMixin`

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `created_at` | `DateTimeField` | Automatically set when the record is created (`auto_now_add=True`) |
| `updated_at` | `DateTimeField` | Automatically updated on every save (`auto_now=True`) |

#### Usage

```python
from django.db import models
from oxutils.models.base import TimestampMixin

class Article(TimestampMixin):
    title = models.CharField(max_length=255)
    content = models.TextField()
```

#### Example

```python
article = Article.objects.create(title="Hello World", content="...")
print(article.created_at)  # 2024-12-01 15:30:00
print(article.updated_at)  # 2024-12-01 15:30:00

article.title = "Updated Title"
article.save()
print(article.updated_at)  # 2024-12-01 15:35:00 (automatically updated)
```

---

### UserTrackingMixin

Tracks which user created and last modified a record.

**Location:** `oxutils.models.base.UserTrackingMixin`

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `created_by` | `ForeignKey` | User who created the record (nullable) |
| `updated_by` | `ForeignKey` | User who last updated the record (nullable) |

#### Usage

```python
from django.db import models
from oxutils.models.base import UserTrackingMixin

class Document(UserTrackingMixin):
    title = models.CharField(max_length=255)
    
    def save(self, *args, user=None, **kwargs):
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)
```

#### Notes

- Uses `settings.AUTH_USER_MODEL` for user references
- Related names use dynamic naming: `%(app_label)s_%(class)s_created` and `%(app_label)s_%(class)s_updated`
- Both fields are nullable and use `SET_NULL` on deletion

---

### SlugMixin

Provides a URL-friendly slug field.

**Location:** `oxutils.models.base.SlugMixin`

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `slug` | `SlugField` | Unique, URL-friendly identifier (max 255 characters) |

#### Usage

```python
from django.db import models
from django.utils.text import slugify
from oxutils.models.base import SlugMixin

class Category(SlugMixin):
    name = models.CharField(max_length=255)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
```

#### Example

```python
category = Category.objects.create(name="Technology & Innovation")
print(category.slug)  # "technology-innovation"
```

---

### NameMixin

Provides standard name and description fields with a default `__str__` method.

**Location:** `oxutils.models.base.NameMixin`

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `CharField` | Name of the record (max 255 characters) |
| `description` | `TextField` | Optional description (blank allowed) |

#### Methods

- `__str__()`: Returns the name of the record

#### Usage

```python
from django.db import models
from oxutils.models.base import NameMixin

class Tag(NameMixin):
    color = models.CharField(max_length=7)  # Hex color
```

#### Example

```python
tag = Tag.objects.create(name="Important", description="High priority items", color="#FF0000")
print(tag)  # "Important"
print(tag.description)  # "High priority items"
```

---

### ActiveMixin

Provides soft-delete functionality through an active status field.

**Location:** `oxutils.models.base.ActiveMixin`

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `is_active` | `BooleanField` | Whether the record is active (default: `True`) |

#### Usage

```python
from django.db import models
from oxutils.models.base import ActiveMixin

class Subscription(ActiveMixin):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    plan = models.CharField(max_length=50)
    
    class Meta:
        # Only show active subscriptions by default
        default_manager_name = 'objects'
    
    @classmethod
    def active_objects(cls):
        return cls.objects.filter(is_active=True)
```

#### Example

```python
# Soft delete
subscription.is_active = False
subscription.save()

# Query only active records
active_subs = Subscription.active_objects()
```

---

### OrderingMixin

Provides manual ordering capability for records.

**Location:** `oxutils.models.base.OrderingMixin`

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `order` | `PositiveIntegerField` | Order for sorting (default: 0) |

#### Meta Options

- Default ordering: `['order']`

#### Usage

```python
from django.db import models
from oxutils.models.base import OrderingMixin

class MenuItem(OrderingMixin):
    title = models.CharField(max_length=255)
    url = models.URLField()
```

#### Example

```python
MenuItem.objects.create(title="Home", url="/", order=1)
MenuItem.objects.create(title="About", url="/about", order=2)
MenuItem.objects.create(title="Contact", url="/contact", order=3)

# Items are automatically ordered by the 'order' field
menu_items = MenuItem.objects.all()  # Already sorted: Home, About, Contact
```

---

### BaseModelMixin

Combines the most commonly used mixins into a single base class.

**Location:** `oxutils.models.base.BaseModelMixin`

#### Includes

- `UUIDPrimaryKeyMixin`: UUID primary key
- `TimestampMixin`: Created/updated timestamps
- `ActiveMixin`: Active status field

#### Usage

```python
from django.db import models
from oxutils.models.base import BaseModelMixin

class Customer(BaseModelMixin):
    """
    Customer model with UUID, timestamps, and active status built-in.
    """
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
```

#### Benefits

- Reduces boilerplate code
- Ensures consistency across models
- Provides essential fields for most use cases

---

## Service Mixins

Service mixins provide standardized exception handling and business logic patterns.

### BaseService

Base class for service layer with comprehensive exception handling.

**Location:** `oxutils.mixins.services.BaseService`

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `logger` | `Logger \| None` | Optional logger instance for the service |

#### Methods

##### `object_accessed(instance_class, instance)`

Logs object access if audit logging is enabled.

**Parameters:**
- `instance_class`: The model class
- `instance`: The model instance being accessed

**Usage:**
```python
def get_user(self, user_id: str):
    user = User.objects.get(id=user_id)
    self.object_accessed(User, user)
    return user
```

##### `inner_exception_handler(exc, logger)`

Override this method to handle service-specific exceptions.

**Parameters:**
- `exc`: The exception to handle
- `logger`: Logger instance

**Returns:** Should raise an `APIException` or re-raise the original exception

**Usage:**
```python
class UserService(BaseService):
    def inner_exception_handler(self, exc, logger):
        if isinstance(exc, UserNotVerifiedException):
            raise ValidationException(detail="User email not verified")
        raise exc
```

##### `exception_handler(exc, logger=None)`

Handles all exceptions with a standardized approach.

**Parameters:**
- `exc`: The exception to handle
- `logger`: Optional logger instance

**Handled Exceptions:**

| Exception Type | Converted To | Description |
|----------------|--------------|-------------|
| `ValidationError` | `ValidationException` | Django validation errors |
| `ObjectDoesNotExist` | `NotFoundException` | Object not found errors |
| `IntegrityError` (unique) | `DuplicateEntryException` | Duplicate entry violations |
| `IntegrityError` (foreign key) | `InvalidParameterException` | Foreign key violations |
| `IntegrityError` (other) | `ConflictException` | Other integrity violations |
| `ValueError` | `InvalidParameterException` | Invalid parameter values |
| `PermissionError` | `PermissionDeniedException` | Permission denied |
| `TypeError` | `InternalErrorException` | Type errors (programming errors) |
| `KeyError` | `MissingParameterException` | Missing required parameters |
| `AttributeError` | `InternalErrorException` | Attribute errors |
| Other | `InternalErrorException` | Unhandled exceptions |

#### Complete Usage Example

```python
from oxutils.mixins.services import BaseService
from oxutils.exceptions import ValidationException
import logging

class OrderService(BaseService):
    logger = logging.getLogger(__name__)
    
    def inner_exception_handler(self, exc, logger):
        """Handle order-specific exceptions"""
        if isinstance(exc, InsufficientStockException):
            raise ValidationException(
                detail="Insufficient stock for this order",
                code="insufficient_stock"
            )
        raise exc
    
    def create_order(self, user_id: str, items: list):
        try:
            # Business logic here
            user = User.objects.get(id=user_id)
            self.object_accessed(User, user)
            
            order = Order.objects.create(user=user)
            
            for item in items:
                # This might raise InsufficientStockException
                self.add_item_to_order(order, item)
            
            return order
            
        except Exception as exc:
            # All exceptions are standardized
            self.exception_handler(exc)
```

---

## Schema Mixins

Schema mixins provide standardized response formats for APIs.

### ResponseSchema

Standardized error response schema for API endpoints.

**Location:** `oxutils.mixins.schemas.ResponseSchema`

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `detail` | `str` | Yes | Human-readable error message |
| `code` | `str` | Yes | Machine-readable error code |
| `errors` | `Dict[str, Any]` | No | Additional error details (e.g., field validation errors) |

#### Usage

```python
from ninja import Router
from oxutils.mixins.schemas import ResponseSchema

router = Router()

@router.post(
    "/users",
    response={
        201: UserSchema,
        400: ResponseSchema,
        409: ResponseSchema
    }
)
def create_user(request, payload: CreateUserSchema):
    """
    Create a new user.
    
    Returns:
        201: User created successfully
        400: Validation error
        409: User already exists
    """
    # Implementation
    pass
```

#### Example Response

```json
{
  "detail": "Validation failed",
  "code": "validation_error",
  "errors": {
    "email": ["This email is already registered"],
    "password": ["Password must be at least 8 characters"]
  }
}
```

---

## Exception Mixins

Exception mixins enhance exception classes with structured error information.

### DetailDictMixin

Builds structured error dictionaries for API exceptions.

**Location:** `oxutils.mixins.base.DetailDictMixin`

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `default_detail` | `str` | Default error message |
| `default_code` | `str` | Default error code |

#### Constructor

```python
def __init__(self, detail=None, code=None) -> None
```

**Parameters:**
- `detail`: Custom error message (string) or error dictionary
- `code`: Custom error code

#### Usage

```python
from rest_framework.exceptions import APIException
from oxutils.mixins.base import DetailDictMixin

class CustomException(DetailDictMixin, APIException):
    status_code = 400
    default_detail = "A custom error occurred"
    default_code = "custom_error"

# Usage examples
raise CustomException()  
# {"detail": "A custom error occurred", "code": "custom_error"}

raise CustomException(detail="Specific error message")
# {"detail": "Specific error message", "code": "custom_error"}

raise CustomException(detail={"field": "error"}, code="field_error")
# {"detail": "A custom error occurred", "code": "field_error", "field": "error"}
```

---

## Best Practices

### Model Mixins

1. **Order matters**: Place mixins before the main model class
   ```python
   class MyModel(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
       pass
   ```

2. **Use BaseModelMixin** for most cases to reduce boilerplate

3. **Combine mixins** as needed for specific requirements
   ```python
   class Product(BaseModelMixin, NameMixin, SlugMixin):
       price = models.DecimalField(max_digits=10, decimal_places=2)
   ```

### Service Mixins

1. **Always use exception_handler**: Wrap service methods with exception handling
   ```python
   def my_service_method(self):
       try:
           # Business logic
           pass
       except Exception as exc:
           self.exception_handler(exc)
   ```

2. **Override inner_exception_handler**: For domain-specific exceptions

3. **Use logging**: Set the `logger` attribute for better debugging

### Schema Mixins

1. **Document all responses**: Use `ResponseSchema` in API endpoint decorators

2. **Provide clear error codes**: Use descriptive, machine-readable codes

### Exception Mixins

1. **Inherit from DetailDictMixin**: For all custom API exceptions

2. **Set meaningful defaults**: Provide clear `default_detail` and `default_code`

---

## Migration Guide

### From Standard Django Models

**Before:**
```python
class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=255)
```

**After:**
```python
from oxutils.models.base import BaseModelMixin, NameMixin

class Product(BaseModelMixin, NameMixin):
    pass  # All fields are inherited!
```

### From Manual Exception Handling

**Before:**
```python
def create_user(email, password):
    try:
        user = User.objects.create(email=email, password=password)
        return user
    except IntegrityError:
        raise ValidationError("User already exists")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
```

**After:**
```python
from oxutils.mixins.services import BaseService

class UserService(BaseService):
    def create_user(self, email, password):
        try:
            user = User.objects.create(email=email, password=password)
            return user
        except Exception as exc:
            self.exception_handler(exc)  # Automatically handles all cases
```

---

## Related Documentation

- [Exceptions & Utilities](./misc.md) - Custom exceptions and utility functions
- [Settings & Configuration](./settings.md) - Configuration management
- [Enums](./enums.md) - Standardized enumerations
- [Audit System](./audit.md) - Audit logging and tracking

---

## Support

For questions or issues, please contact the Oxiliere development team or open an issue in the repository.
