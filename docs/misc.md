# Exceptions & Utilities Documentation

## Overview

OxUtils provides a comprehensive set of custom exceptions and utility functions for Django and Django Ninja applications. The exceptions system offers standardized error handling with consistent error codes and messages, while utility functions simplify common operations like URL building, request validation, and file uploads.

### Key Features

- **Standardized Exceptions**: Consistent error responses across APIs
- **Error Codes**: Machine-readable error codes for all exceptions
- **Internationalization**: Built-in i18n support for error messages
- **Ninja Integration**: Seamless integration with Django Ninja
- **Utility Functions**: Common operations simplified
- **Type Safety**: Type hints for better IDE support

---

## Table of Contents

- [Exceptions](#exceptions)
  - [Exception Hierarchy](#exception-hierarchy)
  - [Error Codes](#error-codes)
  - [Available Exceptions](#available-exceptions)
  - [Usage Examples](#usage-examples)
- [Utility Functions](#utility-functions)
  - [URL Functions](#url-functions)
  - [Request Functions](#request-functions)
  - [Validation Functions](#validation-functions)
- [Best Practices](#best-practices)
- [Integration Patterns](#integration-patterns)

---

## Exceptions

### Exception Hierarchy

```
Exception
└── OxException
    └── APIException (with DetailDictMixin)
        ├── NotFoundException (404)
        ├── ValidationException (400)
        ├── ConflictException (409)
        ├── DuplicateEntryException (409)
        ├── PermissionDeniedException (403)
        ├── UnauthorizedException (401)
        ├── InvalidParameterException (400)
        ├── MissingParameterException (400)
        └── InternalErrorException (500)
```

### Base Exception Classes

#### OxException

Base exception class for all OxUtils exceptions.

```python
class OxException(Exception):
    pass
```

#### APIException

Base API exception with structured error responses.

**Location:** `oxutils.exceptions.APIException`

**Attributes:**
- `status_code`: HTTP status code (default: 500)
- `default_code`: Machine-readable error code
- `default_detail`: Human-readable error message

**Response Format:**
```json
{
  "detail": "Error message",
  "code": "error_code"
}
```

---

### Error Codes

All error codes are defined in `ExceptionCode` class.

**Location:** `oxutils.exceptions.ExceptionCode`

#### HTTP 4xx Client Errors

| Code | Value | Description |
|------|-------|-------------|
| `BAD_REQUEST` | `"bad_request"` | Invalid request format |
| `UNAUTHORIZED` | `"unauthorized"` | Authentication required |
| `FORBIDDEN` | `"forbidden"` | Access forbidden |
| `NOT_FOUND` | `"not_found"` | Resource not found |
| `METHOD_NOT_ALLOWED` | `"method_not_allowed"` | HTTP method not allowed |
| `NOT_ACCEPTABLE` | `"not_acceptable"` | Content type not acceptable |
| `CONFLICT_ERROR` | `"conflict_error"` | Resource conflict |
| `DUPLICATE_ENTRY` | `"duplicate_entry"` | Duplicate resource |
| `VALIDATION_ERROR` | `"validation_error"` | Validation failed |
| `INVALID_INPUT` | `"invalid_input"` | Invalid input data |
| `MISSING_PARAMETER` | `"missing_parameter"` | Required parameter missing |
| `INVALID_PARAMETER` | `"invalid_parameter"` | Invalid parameter value |
| `PAYMENT_REQUIRED` | `"payment_required"` | Payment required |
| `PRECONDITION_FAILED` | `"precondition_failed"` | Precondition not met |

#### HTTP 5xx Server Errors

| Code | Value | Description |
|------|-------|-------------|
| `INTERNAL_ERROR` | `"internal_error"` | Internal server error |
| `FAILED_ERROR` | `"failed_error"` | Operation failed |
| `SERVICE_UNAVAILABLE` | `"service_unavailable"` | Service unavailable |
| `TIMEOUT` | `"timeout"` | Request timeout |

#### Authentication & Authorization

| Code | Value | Description |
|------|-------|-------------|
| `AUTHENTICATION_FAILED` | `"authentication_failed"` | Authentication failed |
| `PERMISSION_DENIED` | `"permission_denied"` | Permission denied |
| `INSUFFICIENT_PERMISSIONS` | `"insufficient_permissions"` | Insufficient permissions |
| `INVALID_TOKEN` | `"invalid_token"` | Invalid authentication token |
| `INVALID_ORGANIZATION_TOKEN` | `"invalid_org_token"` | Invalid organization token |
| `EXPIRED_TOKEN` | `"expired_token"` | Token expired |
| `INVALID_CREDENTIALS` | `"invalid_credentials"` | Invalid credentials |

#### Account Status

| Code | Value | Description |
|------|-------|-------------|
| `ACCOUNT_DISABLED` | `"account_disabled"` | Account disabled |
| `ACCOUNT_NOT_VERIFIED` | `"account_not_verified"` | Account not verified |

#### Resource Management

| Code | Value | Description |
|------|-------|-------------|
| `RESOURCE_LOCKED` | `"resource_locked"` | Resource locked |
| `RESOURCE_EXHAUSTED` | `"resource_exhausted"` | Resource exhausted |
| `QUOTA_EXCEEDED` | `"quota_exceeded"` | Quota exceeded |
| `RATE_LIMIT_EXCEEDED` | `"rate_limit_exceeded"` | Rate limit exceeded |
| `OPERATION_NOT_PERMITTED` | `"operation_not_permitted"` | Operation not permitted |

#### Success Code

| Code | Value | Description |
|------|-------|-------------|
| `SUCCESS` | `"success"` | Operation successful |

---

### Available Exceptions

#### NotFoundException

Resource not found error (404).

**Location:** `oxutils.exceptions.NotFoundException`

```python
class NotFoundException(APIException):
    status_code = 404
    default_code = ExceptionCode.NOT_FOUND
    default_detail = _('The requested resource does not exist')
```

**Usage:**
```python
from oxutils.exceptions import NotFoundException

# Basic usage
raise NotFoundException()

# With custom message
raise NotFoundException(detail="User not found")

# With additional data
raise NotFoundException(detail={
    "message": "User not found",
    "user_id": user_id
})
```

---

#### ValidationException

Validation error (400).

**Location:** `oxutils.exceptions.ValidationException`

```python
class ValidationException(APIException):
    status_code = 400
    default_code = ExceptionCode.VALIDATION_ERROR
    default_detail = _('Validation error')
```

**Usage:**
```python
from oxutils.exceptions import ValidationException

# Basic usage
raise ValidationException()

# With field errors
raise ValidationException(detail={
    "email": ["Invalid email format"],
    "password": ["Password too short"]
})

# With custom message
raise ValidationException(detail="Invalid input data")
```

---

#### ConflictException

Resource conflict error (409).

**Location:** `oxutils.exceptions.ConflictException`

```python
class ConflictException(APIException):
    status_code = 409
    default_code = ExceptionCode.CONFLICT_ERROR
    default_detail = _('The operation conflicts with existing data')
```

**Usage:**
```python
from oxutils.exceptions import ConflictException

# Basic usage
raise ConflictException()

# With details
raise ConflictException(detail="Cannot delete user with active orders")
```

---

#### DuplicateEntryException

Duplicate resource error (409).

**Location:** `oxutils.exceptions.DuplicateEntryException`

```python
class DuplicateEntryException(APIException):
    status_code = 409
    default_code = ExceptionCode.DUPLICATE_ENTRY
    default_detail = _('A resource with these details already exists')
```

**Usage:**
```python
from oxutils.exceptions import DuplicateEntryException

# Basic usage
raise DuplicateEntryException()

# With details
raise DuplicateEntryException(detail="Email already registered")
```

---

#### PermissionDeniedException

Permission denied error (403).

**Location:** `oxutils.exceptions.PermissionDeniedException`

```python
class PermissionDeniedException(APIException):
    status_code = 403
    default_code = ExceptionCode.PERMISSION_DENIED
    default_detail = _('You do not have permission to perform this action')
```

**Usage:**
```python
from oxutils.exceptions import PermissionDeniedException

# Basic usage
raise PermissionDeniedException()

# With details
raise PermissionDeniedException(detail="Admin access required")
```

---

#### UnauthorizedException

Authentication required error (401).

**Location:** `oxutils.exceptions.UnauthorizedException`

```python
class UnauthorizedException(APIException):
    status_code = 401
    default_code = ExceptionCode.UNAUTHORIZED
    default_detail = _('Authentication is required')
```

**Usage:**
```python
from oxutils.exceptions import UnauthorizedException

# Basic usage
raise UnauthorizedException()

# With details
raise UnauthorizedException(detail="Invalid or expired token")
```

---

#### InvalidParameterException

Invalid parameter error (400).

**Location:** `oxutils.exceptions.InvalidParameterException`

```python
class InvalidParameterException(APIException):
    status_code = 400
    default_code = ExceptionCode.INVALID_PARAMETER
    default_detail = _('Invalid parameter provided')
```

**Usage:**
```python
from oxutils.exceptions import InvalidParameterException

# Basic usage
raise InvalidParameterException()

# With details
raise InvalidParameterException(detail="Invalid date format")
```

---

#### MissingParameterException

Missing parameter error (400).

**Location:** `oxutils.exceptions.MissingParameterException`

```python
class MissingParameterException(APIException):
    status_code = 400
    default_code = ExceptionCode.MISSING_PARAMETER
    default_detail = _('Required parameter is missing')
```

**Usage:**
```python
from oxutils.exceptions import MissingParameterException

# Basic usage
raise MissingParameterException()

# With details
raise MissingParameterException(detail="Required field 'email' is missing")
```

---

#### InternalErrorException

Internal server error (500).

**Location:** `oxutils.exceptions.InternalErrorException`

```python
class InternalErrorException(APIException):
    status_code = 500
    default_code = ExceptionCode.INTERNAL_ERROR
    default_detail = _('An unexpected error occurred while processing your request')
```

**Usage:**
```python
from oxutils.exceptions import InternalErrorException

# Basic usage
raise InternalErrorException()

# With details (for logging, not exposed to client)
raise InternalErrorException(detail="Database connection failed")
```

---

### Usage Examples

#### Basic Exception Handling

```python
from ninja import Router
from oxutils.exceptions import NotFoundException, ValidationException

router = Router()

@router.get("/users/{user_id}")
def get_user(request, user_id: str):
    try:
        user = User.objects.get(id=user_id)
        return user
    except User.DoesNotExist:
        raise NotFoundException(detail=f"User {user_id} not found")
```

#### Validation with Custom Errors

```python
from oxutils.exceptions import ValidationException

def validate_age(age: int):
    if age < 18:
        raise ValidationException(detail="User must be at least 18 years old")
    if age > 120:
        raise ValidationException(detail="Invalid age provided")

@router.post("/users")
def create_user(request, payload: UserSchema):
    validate_age(payload.age)
    # Create user
```

#### Permission Checking

```python
from oxutils.exceptions import PermissionDeniedException

def check_admin_permission(user):
    if not user.is_staff:
        raise PermissionDeniedException(detail="Admin access required")

@router.delete("/users/{user_id}")
def delete_user(request, user_id: str):
    check_admin_permission(request.user)
    # Delete user
```

#### Service Layer Exception Handling

```python
from oxutils.exceptions import (
    NotFoundException,
    DuplicateEntryException,
    InternalErrorException
)

class UserService:
    def create_user(self, email: str, password: str):
        try:
            # Check for duplicate
            if User.objects.filter(email=email).exists():
                raise DuplicateEntryException(detail="Email already registered")
            
            # Create user
            user = User.objects.create(email=email, password=password)
            return user
            
        except DuplicateEntryException:
            raise
        except Exception as e:
            logger.error(f"User creation failed: {e}")
            raise InternalErrorException()
```

---

## Utility Functions

### URL Functions

#### get_absolute_url

Build absolute URL from relative path.

**Location:** `oxutils.functions.get_absolute_url`

**Signature:**
```python
def get_absolute_url(url: str, request=None) -> str
```

**Parameters:**
- `url` (str): Relative URL path
- `request` (optional): Django request object

**Returns:** Absolute URL string

**Usage:**
```python
from oxutils.functions import get_absolute_url

# With request object
absolute_url = get_absolute_url('/media/image.jpg', request)
# Returns: http://example.com/media/image.jpg

# Without request (uses SITE_URL setting)
absolute_url = get_absolute_url('/media/image.jpg')
# Returns: http://localhost:8000/media/image.jpg
```

**Example in Views:**
```python
from oxutils.functions import get_absolute_url

@router.post("/upload")
def upload_file(request, file: UploadedFile):
    # Save file
    path = default_storage.save(f'uploads/{file.name}', file)
    
    # Get absolute URL
    absolute_url = get_absolute_url(default_storage.url(path), request)
    
    return {"url": absolute_url}
```

---

### Request Functions

#### request_is_bound

Check if a request contains data (similar to Django Form.is_bound).

**Location:** `oxutils.functions.request_is_bound`

**Signature:**
```python
def request_is_bound(request) -> bool
```

**Parameters:**
- `request`: Django HttpRequest or DRF Request object

**Returns:** `True` if request has data, `False` otherwise

**Usage:**
```python
from oxutils.functions import request_is_bound

@router.post("/users")
def create_user(request):
    if not request_is_bound(request):
        raise ValidationException(detail="No data provided")
    
    # Process request
```

**Checks:**
- Request has `data` attribute (DRF)
- Request has `POST` data
- Request has `FILES`
- Request method is POST, PUT, or PATCH

---

#### get_request_data

Extract data from request (works with Django and DRF).

**Location:** `oxutils.functions.get_request_data`

**Signature:**
```python
def get_request_data(request) -> dict
```

**Parameters:**
- `request`: Django HttpRequest or DRF Request object

**Returns:** Dictionary of request data (empty dict if no data)

**Usage:**
```python
from oxutils.functions import get_request_data

@router.post("/process")
def process_data(request):
    data = get_request_data(request)
    
    # Access data
    email = data.get('email')
    name = data.get('name')
    
    # Process data
```

**Compatibility:**
- Django REST Framework: Uses `request.data`
- Django HttpRequest: Uses `request.POST`
- Returns empty dict if no data

---

### Validation Functions

#### validate_image

Validate uploaded image file.

**Location:** `oxutils.functions.validate_image`

**Signature:**
```python
def validate_image(image: UploadedFile, size: int = 2) -> None
```

**Parameters:**
- `image` (UploadedFile): Uploaded file to validate
- `size` (int): Maximum file size in MB (default: 2)

**Raises:** `ValidationError` if validation fails

**Validations:**
1. **File Size**: Maximum size (default 2MB)
2. **Content Type**: Must be image MIME type
3. **File Extension**: Must be valid image extension
4. **Image Verification**: Uses PIL to verify it's a valid image

**Allowed Types:**
- `image/jpeg`
- `image/jpg`
- `image/png`
- `image/gif`
- `image/webp`

**Allowed Extensions:**
- `.jpg`, `.jpeg`
- `.png`
- `.gif`
- `.webp`

**Usage:**
```python
from ninja import Router, File
from ninja.files import UploadedFile
from oxutils.functions import validate_image

router = Router()

@router.post("/upload-avatar")
def upload_avatar(request, avatar: UploadedFile = File(...)):
    # Validate image (2MB max)
    validate_image(avatar, size=2)
    
    # Save image
    path = default_storage.save(f'avatars/{avatar.name}', avatar)
    
    return {"path": path}

@router.post("/upload-banner")
def upload_banner(request, banner: UploadedFile = File(...)):
    # Validate image (5MB max)
    validate_image(banner, size=5)
    
    # Save image
    path = default_storage.save(f'banners/{banner.name}', banner)
    
    return {"path": path}
```

**Error Messages:**
```python
# File too large
"La taille du fichier ne peut pas dépasser 2MB. Taille actuelle: 3.5MB"

# Invalid type
"Type de fichier non supporté. Types autorisés: image/jpeg, image/jpg, image/png, image/gif, image/webp"

# Invalid extension
"Extension de fichier non supportée. Extensions autorisées: .jpg, .jpeg, .png, .gif, .webp"

# Invalid image
"Le fichier n'est pas une image valide"
```

---

## Best Practices

### 1. Use Specific Exceptions

**❌ Bad - Generic exception:**
```python
raise Exception("User not found")
```

**✅ Good - Specific exception:**
```python
from oxutils.exceptions import NotFoundException
raise NotFoundException(detail="User not found")
```

### 2. Provide Meaningful Error Messages

**❌ Bad - Vague message:**
```python
raise ValidationException(detail="Error")
```

**✅ Good - Descriptive message:**
```python
raise ValidationException(detail="Email format is invalid. Expected: user@example.com")
```

### 3. Include Context in Errors

**❌ Bad - No context:**
```python
raise NotFoundException()
```

**✅ Good - With context:**
```python
raise NotFoundException(detail={
    "message": "Order not found",
    "order_id": order_id,
    "user_id": user_id
})
```

### 4. Handle Exceptions at Service Layer

```python
class OrderService:
    def get_order(self, order_id: str):
        try:
            order = Order.objects.get(id=order_id)
            return order
        except Order.DoesNotExist:
            raise NotFoundException(detail=f"Order {order_id} not found")
        except Exception as e:
            logger.error(f"Failed to get order: {e}")
            raise InternalErrorException()
```

### 5. Use Error Codes for Client Logic

```python
# Client-side handling
try:
    response = api.get_user(user_id)
except APIError as e:
    if e.code == 'not_found':
        show_not_found_message()
    elif e.code == 'unauthorized':
        redirect_to_login()
    else:
        show_generic_error()
```

### 6. Validate Early

```python
from oxutils.functions import validate_image

@router.post("/upload")
def upload_file(request, file: UploadedFile = File(...)):
    # Validate immediately
    validate_image(file, size=5)
    
    # Then process
    path = save_file(file)
    return {"path": path}
```

### 7. Log Internal Errors

```python
from oxutils.exceptions import InternalErrorException
import structlog

logger = structlog.get_logger(__name__)

try:
    result = complex_operation()
except Exception as e:
    logger.error("Operation failed", error=str(e), exc_info=True)
    raise InternalErrorException()  # Don't expose internal details
```

---

## Integration Patterns

### Django Ninja API

```python
from ninja import Router
from oxutils.exceptions import (
    NotFoundException,
    ValidationException,
    PermissionDeniedException
)

router = Router()

@router.get("/users/{user_id}", response={
    200: UserSchema,
    404: dict,
    403: dict
})
def get_user(request, user_id: str):
    """Get user by ID."""
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

### Service Layer Pattern

```python
from oxutils.exceptions import (
    NotFoundException,
    ValidationException,
    DuplicateEntryException
)
from oxutils.mixins.services import BaseService

class UserService(BaseService):
    def create_user(self, email: str, password: str):
        """Create new user."""
        try:
            # Validate
            if not email:
                raise ValidationException(detail="Email is required")
            
            # Check duplicate
            if User.objects.filter(email=email).exists():
                raise DuplicateEntryException(detail="Email already registered")
            
            # Create
            user = User.objects.create(email=email, password=password)
            return user
            
        except (ValidationException, DuplicateEntryException):
            raise
        except Exception as exc:
            self.exception_handler(exc)
```

### Middleware Error Handling

```python
from oxutils.exceptions import UnauthorizedException
from oxutils.jwt.client import verify_token
import jwt

class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip public endpoints
        if request.path.startswith('/public/'):
            return self.get_response(request)
        
        # Extract token
        token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        
        if not token:
            raise UnauthorizedException(detail="Authentication token required")
        
        # Verify token
        try:
            payload = verify_token(token)
            request.jwt_payload = payload
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException(detail="Token has expired")
        except jwt.InvalidTokenError:
            raise UnauthorizedException(detail="Invalid token")
        
        return self.get_response(request)
```

### Custom Exception

```python
from oxutils.exceptions import APIException, ExceptionCode

class QuotaExceededException(APIException):
    status_code = 429
    default_code = ExceptionCode.QUOTA_EXCEEDED
    default_detail = "API quota exceeded. Please try again later."

# Usage
def check_quota(user):
    if user.api_calls_today >= user.quota:
        raise QuotaExceededException(detail={
            "current": user.api_calls_today,
            "limit": user.quota,
            "reset_at": user.quota_reset_time
        })
```

---

## Testing

### Testing Exceptions

```python
import pytest
from oxutils.exceptions import NotFoundException, ValidationException

def test_not_found_exception():
    """Test NotFoundException."""
    with pytest.raises(NotFoundException) as exc_info:
        raise NotFoundException(detail="User not found")
    
    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value)

def test_validation_exception():
    """Test ValidationException."""
    with pytest.raises(ValidationException) as exc_info:
        raise ValidationException(detail="Invalid email")
    
    assert exc_info.value.status_code == 400
```

### Testing Utility Functions

```python
from oxutils.functions import get_absolute_url, validate_image
from django.test import RequestFactory

def test_get_absolute_url():
    """Test absolute URL generation."""
    factory = RequestFactory()
    request = factory.get('/')
    
    url = get_absolute_url('/media/image.jpg', request)
    assert url.startswith('http://')
    assert '/media/image.jpg' in url

def test_validate_image():
    """Test image validation."""
    # Test with invalid file
    with pytest.raises(ValidationError):
        validate_image(large_file, size=1)
```

---

## Related Documentation

- [Mixins Documentation](./mixins.md) - DetailDictMixin and BaseService
- [JWT Documentation](./jwt.md) - Authentication exceptions
- [API Documentation](./api.md) - API integration patterns

---

## Support

For questions or issues regarding exceptions and utilities, please contact the Oxiliere development team or open an issue in the repository.
