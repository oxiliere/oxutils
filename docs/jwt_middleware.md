# JWT Middleware & Passive Authentication

This documentation covers the JWT middleware system and passive authentication classes for Django applications.

## Overview

The JWT middleware system provides stateless token authentication for Django applications using `ninja-jwt`. It supports:

- **Header-based JWT authentication** (`Authorization: Bearer <token>`)
- **Cookie-based JWT authentication** with CSRF protection
- **Development-only basic auth** (no password required)
- **Passive authentication** for Ninja API views

## Middleware Classes

### JWTAuthBaseMiddleware

Abstract base class for JWT authentication middleware.

```python
from oxutils.jwt.middleware import JWTAuthBaseMiddleware
```

**Features:**
- Stateless authentication (no database lookup)
- Token validation using `ninja-jwt`
- Automatic user assignment to `request.user`
- Structured logging with `structlog`
- Skips authentication if user is already authenticated (middleware chaining)

**Abstract Methods:**
- `get_token_from_request(request)` - Must be implemented by subclasses

### JWTHeaderAuthMiddleware

Extracts and validates JWT tokens from the `Authorization` header.

```python
# settings.py
MIDDLEWARE = [
    # ... other middlewares
    'oxutils.jwt.middleware.JWTHeaderAuthMiddleware',
]
```

**Configuration:**
- `openapi_scheme`: `"bearer"` (default)
- `header`: `"Authorization"` (default)

**Usage:**
```http
Authorization: Bearer <jwt_token>
```

**Validation:**
- Checks for `Bearer` scheme (case-insensitive)
- Validates JWT format (3 parts separated by dots)
- Returns `None` if header is missing or invalid

### JWTCookieAuthMiddleware

Extracts and validates JWT tokens from cookies with CSRF protection.

```python
# settings.py
MIDDLEWARE = [
    # ... other middlewares
    'oxutils.jwt.middleware.JWTCookieAuthMiddleware',
]
```

**Configuration:**
- `param_name`: Cookie name (default: `access_token` from `ACCESS_TOKEN_COOKIE` constant)

**Features:**
- CSRF validation via `check_csrf()`
- Raises `PermissionDenied` if CSRF check fails
- Sets `AnonymousUser` on CSRF failure (does not block request)

**Cookie Structure:**
```python
# Cookie name: "access_token" (configurable)
# Value: <jwt_token>
```

### BasicNoPasswordAuthMiddleware

⚠️ **DEVELOPMENT ONLY** - Basic authentication without password verification.

```python
# settings.py - DEBUG mode only!
MIDDLEWARE = [
    # ... other middlewares
    'oxutils.jwt.middleware.BasicNoPasswordAuthMiddleware',
]
```

**Security:**
- Automatically disabled when `settings.DEBUG = False`
- Logs warning on initialization in DEBUG mode
- Requires only username/email (password is ignored)

**Usage:**
```http
Authorization: Basic base64(username:)
# or
Authorization: Basic base64(username:anything)
```

**Example:**
```bash
# For user "admin@example.com"
# Base64 encode: "admin@example.com:"
echo -n "admin@example.com:" | base64
# Output: YWRtaW5AZXhhbXBsZS5jb206

# Request
curl -H "Authorization: Basic YWRtaW5AZXhhbXBsZS5jb206" http://localhost:8000/api/
```

## Middleware Chaining

Multiple JWT middlewares can be chained together. The first successful authentication sets `request.user`, and subsequent middlewares skip authentication.

```python
# settings.py
MIDDLEWARE = [
    # ... other middlewares
    'oxutils.jwt.middleware.JWTHeaderAuthMiddleware',  # Try header first
    'oxutils.jwt.middleware.JWTCookieAuthMiddleware',  # Fallback to cookie
    'oxutils.jwt.middleware.BasicNoPasswordAuthMiddleware',  # Dev fallback
]
```

**Behavior:**
1. If `JWTHeaderAuthMiddleware` authenticates → `request.user` is set
2. `JWTCookieAuthMiddleware` sees `is_authenticated=True` → skips
3. `BasicNoPasswordAuthMiddleware` sees `is_authenticated=True` → skips

## Passive Authentication Classes

For Ninja API views that need to accept authentication but don't require it (optional auth).

### JWTPassiveAuth

Checks if user was already authenticated by middleware, no active token validation.

```python
from ninja import Router
from oxutils.jwt.auth import jwt_passive_auth

router = Router()

@router.get("/profile", auth=jwt_passive_auth)
def get_profile(request):
    if request.user.is_authenticated:
        return {"user": request.user.email}
    return {"user": None}
```

### JWTCookiePassiveAuth

Cookie-based passive authentication.

```python
from ninja import Router
from oxutils.jwt.auth import jwt_cookie_passive_auth

router = Router()

@router.get("/dashboard", auth=jwt_cookie_passive_auth)
def get_dashboard(request):
    # User may or may not be authenticated
    pass
```

## Auth Handler Functions

### get_passive_auth_handlers()

Returns appropriate auth handlers based on `settings.DEBUG`.

```python
from oxutils.jwt.auth import get_passive_auth_handlers
from ninja import Router

router = Router()

@router.get("/api/data", auth=get_passive_auth_handlers())
def get_data(request):
    """
    In DEBUG: No auth required (empty list)
    In PRODUCTION: Passive auth handlers
    """
    pass
```

**Behavior:**
- `DEBUG=True`: Returns provided `auths` (default: empty list - no auth)
- `DEBUG=False`: Returns `[jwt_passive_auth, jwt_cookie_passive_auth]`

### get_auth_handlers()

Returns active auth handlers for protected endpoints.

```python
from oxutils.jwt.auth import get_auth_handlers

@router.get("/api/protected", auth=get_auth_handlers())
def protected_endpoint(request):
    """
    In DEBUG: Basic auth without password
    In PRODUCTION: JWT header and cookie auth
    """
    pass
```

## Complete Configuration Example

```python
# settings.py

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # JWT Middleware (order matters)
    'oxutils.jwt.middleware.JWTHeaderAuthMiddleware',
    'oxutils.jwt.middleware.JWTCookieAuthMiddleware',
    
    # Dev-only (safe - auto-disabled in production)
    'oxutils.jwt.middleware.BasicNoPasswordAuthMiddleware',
]

# Ninja JWT settings
NINJA_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_COOKIE': 'access_token',
}
```

## API Usage Examples

### Protected Endpoint (Required Auth)

```python
from ninja import Router
from oxutils.jwt.auth import get_auth_handlers

router = Router()

@router.get("/users", auth=get_auth_handlers())
def list_users(request):
    """
    Requires valid JWT token in header or cookie.
    """
    return {"users": []}
```

### Optional Auth Endpoint

```python
from ninja import Router
from oxutils.jwt.auth import get_passive_auth_handlers

router = Router()

@router.get("/public", auth=get_passive_auth_handlers())
def public_data(request):
    """
    Works with or without authentication.
    """
    if request.user.is_authenticated:
        return {"message": f"Hello {request.user.email}"}
    return {"message": "Hello anonymous"}
```

### Manual Middleware Usage

```python
from django.http import JsonResponse

def my_view(request):
    # Middleware has already set request.user
    if request.user.is_authenticated:
        return JsonResponse({"email": request.user.email})
    return JsonResponse({"error": "Not authenticated"}, status=401)
```

## Logging

All middleware uses `structlog` for structured logging:

```python
# Successful authentication
logger.info("dev_auth_success", user_id=1, username="user@example.com")

# Failed authentication
logger.debug("jwt_validation_failed", path="/api/users")

# Security warnings
logger.warning("csrf_check_failed", path="/api/data")
logger.warning("insecure_middleware_loaded")  # Dev middleware
```

## Testing

See `/tests/oxiliere/test_middleware.py` for comprehensive test examples.

## Security Considerations

1. **Always use HTTPS** in production for cookie-based auth
2. **CSRF protection** is mandatory for cookie auth
3. **Remove `BasicNoPasswordAuthMiddleware`** before production (it auto-disables but best to remove)
4. **Token expiration** is handled by `ninja-jwt` validation
5. **No database lookup** - middleware uses stateless `TokenUser`