# Exceptions & Utilities

## Custom Exceptions

All exceptions inherit from `APIException` with standardized format.

### Available Exceptions

```python
from oxutils.exceptions import (
    NotFoundException,           # 404
    ValidationException,         # 400
    ConflictException,          # 409
    DuplicateEntryException,    # 409
    PermissionDeniedException,  # 403
    UnauthorizedException,      # 401
    InvalidParameterException,  # 400
    MissingParameterException,  # 400
    InternalErrorException,     # 500
)
```

### Usage

```python
# Raise exception
if not user:
    raise NotFoundException(detail="User not found")

# With custom code
raise ValidationException(
    detail="Invalid email",
    code="invalid_email"
)

# With dict detail
raise ValidationException(detail={
    "email": "Invalid format",
    "age": "Must be 18+"
})
```

### Response Format

```json
{
  "detail": "User not found",
  "code": "not_found"
}
```

## Utility Functions

### get_absolute_url

```python
from oxutils.functions import get_absolute_url

url = get_absolute_url('/api/users/', request)
# Returns: https://example.com/api/users/
```

### validate_image

```python
from oxutils.functions import validate_image
from ninja_extra.exceptions import ValidationError

try:
    validate_image(uploaded_file, size=2)  # Max 2MB
except ValidationError as e:
    print(e.detail)
```

### request_is_bound

```python
from oxutils.functions import request_is_bound

if request_is_bound(request):
    # Request has data
    data = get_request_data(request)
```

## Related Docs

- [JWT](./jwt.md) - Authentication errors
