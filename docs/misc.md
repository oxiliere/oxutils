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

## S3 Storage Backend

Dynamic S3 storage configuration loaded from environment variables.

### Features

- Environment-driven S3 config (no hardcoded credentials)
- Automatic type conversion (booleans, integers)
- Quote stripping for Docker/K8s env vars
- Kwargs override for programmatic customization
- URL builder for static/media files served via CDN

### `get_s3_storage_backend()`

Loads S3 configuration from environment variables prefixed with `OXI_{TYPE}_STORAGE_`.

```python
from oxutils.s3 import get_s3_storage_backend

# Load S3 config for static files
static_storage = get_s3_storage_backend("static")

# Load S3 config for media files
media_storage = get_s3_storage_backend("media")
```

**Environment variables**:

```bash
# Enable S3 for static files
OXI_STATIC_STORAGE_USE_S3=true

# Required for S3 access
OXI_STATIC_STORAGE_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
OXI_STATIC_STORAGE_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
OXI_STATIC_STORAGE_BUCKET_NAME=my-bucket
OXI_STATIC_STORAGE_ENDPOINT_URL=https://s3.amazonaws.com

# Optional
OXI_STATIC_STORAGE_REGION_NAME=us-east-1
OXI_STATIC_STORAGE_CUSTOM_DOMAIN=cdn.example.com
OXI_STATIC_STORAGE_DEFAULT_ACL=public-read
OXI_STATIC_STORAGE_USE_SSL=true
OXI_STATIC_STORAGE_SIGNATURE_VERSION=s3v4
OXI_STATIC_STORAGE_LOCATION=static
```

**Return value**:

```python
# When USE_S3 is true
{
    "BACKEND": "storages.backends.s3.S3Storage",
    "OPTIONS": {
        "access_key": "AKIA...",
        "secret_key": "wJalr...",
        "bucket_name": "my-bucket",
        "endpoint_url": "https://s3.amazonaws.com",
        # ... other options from env vars
    }
}

# When USE_S3 is false, "0", "False", or ""
None
```

**Type conversion rules**:

| Env value | Python result |
|-----------|--------------|
| `"true"`, `"True"`, `"TRUE"`, `"1"`, `"yes"` | `bool` `True` |
| `"false"`, `"False"`, `"FALSE"` | `bool` `False` |
| `"3600"`, `"1048576"` | `int` |
| `'"quoted"'`, `"'single-quoted'"` | stripped string |
| `'""'`, `"''"` | omitted (empty after stripping) |

**Kwargs override**:

```python
# Env vars provide defaults, kwargs win
storage = get_s3_storage_backend(
    "static",
    bucket_name="override-bucket",   # Overrides env var
    custom_domain="custom.cdn.com",  # New option
    # All kwargs become OPTIONS keys
)
```

**All supported env variables**:

| Env suffix | Option key |
|-----------|-----------|
| `ACCESS_KEY_ID` | `access_key` |
| `SECRET_ACCESS_KEY` | `secret_key` |
| `BUCKET_NAME` | `bucket_name` |
| `ENDPOINT_URL` | `endpoint_url` |
| `REGION_NAME` | `region_name` |
| `DEFAULT_ACL` | `default_acl` |
| `LOCATION` | `location` |
| `CUSTOM_DOMAIN` | `custom_domain` |
| `SIGNATURE_VERSION` | `signature_version` |
| `ADDRESSING_STYLE` | `addressing_style` |
| `USE_SSL` | `use_ssl` |
| `VERIFY` | `verify` |
| `QUERYSTRING_AUTH` | `querystring_auth` |
| `QUERYSTRING_EXPIRE` | `querystring_expire` |
| `FILE_OVERWRITE` | `file_overwrite` |
| `GZIP` | `gzip` |
| `URL_PROTOCOL` | `url_protocol` |
| `SECURITY_TOKEN` | `security_token` |
| `SESSION_PROFILE` | `session_profile` |
| `OBJECT_PARAMETERS` | `object_parameters` |
| `MAX_MEMORY_SIZE` | `max_memory_size` |
| `GZIP_CONTENT_TYPES` | `gzip_content_types` |
| `PROXIES` | `proxies` |
| `CLOUDFRONT_KEY` | `cloudfront_key` |
| `CLOUDFRONT_KEY_ID` | `cloudfront_key_id` |
| `CLOUDFRONT_SIGNER` | `cloudfront_signer` |
| `CLIENT_CONFIG` | `client_config` |

### `get_s3_static_url()`

Builds a URL from S3 storage options, typically for serving static/media files through a CDN.

```python
from oxutils.s3 import get_s3_static_url

options = get_s3_storage_backend("static")
url = get_s3_static_url(options)
if url:
    print(url)  # https://cdn.example.com/static/
```

**Behavior**:

| `custom_domain` | `location` | `url_protocol` | Result |
|----------------|-----------|---------------|--------|
| `None` | — | — | `None` |
| `cdn.example.com` | `""` | default `https` | `https://cdn.example.com/` |
| `cdn.example.com` | `"static"` | default `https` | `https://cdn.example.com/static/` |
| `cdn.example.com` | `"uploads/images"` | `"http"` | `http://cdn.example.com/uploads/images/` |
| `cdn.example.com` | — | `"http"` | `http://cdn.example.com/` |

### Django Integration

Use with `django-storages`:

```python
# settings.py
from oxutils.s3 import get_s3_storage_backend, get_s3_static_url

# Static files
STATICFILES_STORAGE = "storages.backends.s3.S3Storage"
static_options = get_s3_storage_backend("static")
if static_options:
    STORAGES = {
        "staticfiles": static_options,
        "default": static_options,
    }
    STATIC_URL = get_s3_static_url(static_options)
```

### Benefits

- **No credentials in code**: everything comes from the environment
- **Per-environment config**: different buckets/endpoints for dev/staging/prod
- **Optional S3**: when `USE_S3` is false, falls back to local storage
- **Docker/K8s compatible**: strips quotes that Docker sometimes adds to env vars
