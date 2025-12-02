# Mixins

**Reusable Django model and service mixins**

## Model Mixins

### UUIDPrimaryKeyMixin

```python
from oxutils.models.base import UUIDPrimaryKeyMixin

class Product(UUIDPrimaryKeyMixin):
    name = models.CharField(max_length=255)
    # id = UUID field (auto-generated)
```

### TimestampMixin

```python
from oxutils.models.base import TimestampMixin

class Product(TimestampMixin):
    name = models.CharField(max_length=255)
    # created_at, updated_at (auto-managed)
```

### BaseModelMixin

Combines UUID + Timestamps + Active status

```python
from oxutils.models.base import BaseModelMixin

class Product(BaseModelMixin):
    name = models.CharField(max_length=255)
    # id (UUID)
    # created_at, updated_at
    # is_active (default=True)
```

### NameMixin

```python
from oxutils.models.base import NameMixin

class Category(NameMixin):
    # name, description fields
    pass
```

### UserTrackingMixin

```python
from oxutils.models.base import UserTrackingMixin

class Document(UserTrackingMixin):
    title = models.CharField(max_length=255)
    # created_by, updated_by (ForeignKey to User)
```

## Service Mixins

### BaseService

Provides centralized exception handling for service classes.

```python
from oxutils.mixins.services import BaseService
from oxutils.exceptions import ValidationException

class ProductService(BaseService):
    def create_product(self, data):
        try:
            if not data.get('name'):
                raise ValidationException(detail="Name required")
            return Product.objects.create(**data)
        except ValidationException:
            raise  # Re-raise known exceptions
        except Exception as e:
            self.exception_handler(e)  # Convert to InternalErrorException
```

#### exception_handler(exc: Exception, logger: Logger = None)

Handles all exceptions with standardized error conversion.

**Behavior:**
1. Calls `inner_exception_handler(exc, logger)` for custom handling
2. If `inner_exception_handler` raises an `APIException`, re-raises it
3. Otherwise, converts common exceptions:
   - `ValidationError` → `ValidationException`
   - `ObjectDoesNotExist` → `NotFoundException`
   - `IntegrityError` → `DuplicateEntryException` or `ConflictException`
   - `ValueError` → `InvalidParameterException`
   - `KeyError` → `MissingParameterException`
   - Unknown exceptions → `InternalErrorException`

```python
class OrderService(BaseService):
    def process_order(self, order_id):
        try:
            order = Order.objects.get(id=order_id)
            order.process()
            return order
        except Exception as e:
            # Automatically converts to appropriate APIException
            self.exception_handler(e)
```

#### inner_exception_handler(exc: Exception, logger: Logger) - Customizable

Override this method to handle service-specific exceptions before standard conversion.

**Must either:**
- Raise an `APIException` subclass (will be re-raised)
- Re-raise the original exception (will be handled by standard logic)

```python
from oxutils.mixins.services import BaseService
from oxutils.exceptions import ValidationException
from stripe.error import StripeError

class PaymentService(BaseService):
    def inner_exception_handler(self, exc: Exception, logger):
        """Handle payment-specific exceptions."""
        # Handle Stripe errors
        if isinstance(exc, StripeError):
            logger.error("stripe_error", error=str(exc))
            raise ValidationException(
                detail=f"Payment error: {exc.user_message}",
                code="payment_failed"
            )
        
        # Let other exceptions be handled by standard logic
        raise exc
    
    def process_payment(self, amount):
        try:
            return stripe.Charge.create(amount=amount)
        except Exception as e:
            # StripeError → ValidationException (via inner_exception_handler)
            # Other errors → Standard conversion
            self.exception_handler(e)
```

## Schema Mixins

### ResponseSchema

```python
from oxutils.mixins.schemas import ResponseSchema

# Use for API error responses
class ErrorResponse(ResponseSchema):
    # detail: str
    # code: str
    # errors: Optional[Dict]
    pass
```

## Combined Example

```python
from oxutils.models.base import BaseModelMixin, NameMixin

class Product(BaseModelMixin, NameMixin):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # Includes: id, created_at, updated_at, is_active, name, description
```

## Related Docs

- [Settings](./settings.md) - Configuration
- [Exceptions](./misc.md) - Error handling
