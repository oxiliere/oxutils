# JWT Authentication Documentation

## Overview

OxUtils provides a robust JWT (JSON Web Token) authentication system for securing APIs in the Oxiliere ecosystem. The implementation supports RS256 asymmetric encryption, JWKS (JSON Web Key Set) integration, and automatic key caching for optimal performance.

### Key Features

- **RS256 Algorithm**: Asymmetric encryption using RSA public/private key pairs
- **JWKS Support**: Automatic fetching and caching of public keys from authentication servers
- **Key Caching**: Intelligent caching with TTL to minimize external requests
- **Token Verification**: Comprehensive token validation and decoding
- **Django Integration**: Seamless integration with Django settings
- **Key Rotation**: Support for key rotation with cache invalidation

---

## Table of Contents

- [Architecture](#architecture)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Authentication Methods](#authentication-methods)
  - [JWKS-based Authentication](#jwks-based-authentication)
  - [Local Key Authentication](#local-key-authentication)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [Integration Patterns](#integration-patterns)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

---

## Architecture

### Token Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Client    │         │  Auth Server │         │   Service   │
└──────┬──────┘         └──────┬───────┘         └──────┬──────┘
       │                       │                        │
       │  1. Login Request     │                        │
       ├──────────────────────>│                        │
       │                       │                        │
       │  2. JWT Token         │                        │
       │<──────────────────────┤                        │
       │                       │                        │
       │  3. API Request + JWT │                        │
       ├───────────────────────┴───────────────────────>│
       │                                                 │
       │                       4. Fetch JWKS (cached)   │
       │                       ┌────────────────────────┤
       │                       │                        │
       │                       5. Verify Token          │
       │                       └───────────────────────>│
       │                                                 │
       │  6. Response                                    │
       │<────────────────────────────────────────────────┤
       │                                                 │
```

### Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **JWT Client** | Token verification with JWKS | `oxutils.jwt.client` |
| **JWT Auth** | Local key management | `oxutils.jwt.auth` |
| **Constants** | Algorithm configuration | `oxutils.jwt.constants` |
| **Settings** | Configuration management | `oxutils.settings` |

---

## Installation & Setup

### Prerequisites

Install required dependencies:

```bash
pip install PyJWT cryptography jwcrypto requests
```

Or with uv:

```bash
uv add PyJWT cryptography jwcrypto requests
```

### Basic Setup

1. **Configure environment variables:**

```bash
# For JWKS-based authentication (recommended for microservices)
export OXI_JWT_JWKS_URL="https://auth.example.com/.well-known/jwks.json"

# For local key authentication
export OXI_JWT_VERIFYING_KEY="/path/to/public_key.pem"
export OXI_JWT_SIGNING_KEY="/path/to/private_key.pem"

# Token key names (optional)
export OXI_JWT_ACCESS_TOKEN_KEY="access_token"
export OXI_JWT_ORG_ACCESS_TOKEN_KEY="org_access_token"
```

2. **Import settings in Django:**

```python
# settings.py
from oxutils.settings import oxi_settings

# JWT settings are automatically loaded
JWT_JWKS_URL = oxi_settings.jwt_jwks_url
JWT_VERIFYING_KEY = oxi_settings.jwt_verifying_key
```

---

## Configuration

### Settings Reference

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `OXI_JWT_SIGNING_KEY` | `str` | `None` | Path to private key for signing tokens |
| `OXI_JWT_VERIFYING_KEY` | `str` | `None` | Path to public key for verifying tokens |
| `OXI_JWT_JWKS_URL` | `str` | `None` | URL to fetch JWKS from authentication server |
| `OXI_JWT_ACCESS_TOKEN_KEY` | `str` | `"access_token"` | Key name for access token in requests |
| `OXI_JWT_ORG_ACCESS_TOKEN_KEY` | `str` | `"org_access_token"` | Key name for organization token |

### Algorithm Configuration

The system uses RS256 (RSA Signature with SHA-256) by default:

**Location:** `oxutils.jwt.constants.JWT_ALGORITHM`

```python
JWT_ALGORITHM = ["RS256"]
```

### Cache Configuration

JWKS cache settings (defined in `client.py`):

```python
_jwks_cache_ttl = timedelta(hours=1)  # Cache TTL: 1 hour
```

---

## Authentication Methods

### JWKS-based Authentication

**Recommended for microservices architecture**

JWKS (JSON Web Key Set) allows services to fetch public keys from a central authentication server.

#### Setup

```python
# settings.py
OXI_JWT_JWKS_URL = "https://auth.example.com/.well-known/jwks.json"
```

#### Usage

```python
from oxutils.jwt.client import verify_token

def authenticate_request(request):
    """Authenticate request using JWKS."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    try:
        payload = verify_token(token)
        return payload
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")
```

#### JWKS Format

Expected JWKS format from authentication server:

```json
{
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "main",
      "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx...",
      "e": "AQAB",
      "alg": "RS256"
    }
  ]
}
```

---

### Local Key Authentication

**Recommended for standalone services or development**

Use local public/private key pairs for token signing and verification.

#### Generate Keys

```bash
# Generate private key
openssl genrsa -out private_key.pem 2048

# Extract public key
openssl rsa -in private_key.pem -pubout -out public_key.pem
```

#### Setup

```python
# settings.py
OXI_JWT_VERIFYING_KEY = "/path/to/public_key.pem"
OXI_JWT_SIGNING_KEY = "/path/to/private_key.pem"
```

#### Usage

```python
from oxutils.jwt.auth import get_jwks

def get_public_keys():
    """Get public keys for token verification."""
    try:
        jwks = get_jwks()
        return jwks
    except ImproperlyConfigured as e:
        logger.error("JWT configuration error", error=str(e))
        raise
```

---

## API Reference

### Client Module (`oxutils.jwt.client`)

#### `get_jwks_url() -> str`

Get JWKS URL from settings.

**Returns:** The configured JWKS URL

**Raises:** `ImproperlyConfigured` if not configured

```python
from oxutils.jwt.client import get_jwks_url

jwks_url = get_jwks_url()
print(f"JWKS URL: {jwks_url}")
```

---

#### `fetch_jwks(force_refresh: bool = False) -> Dict[str, Any]`

Fetch JWKS from authentication server with caching.

**Parameters:**
- `force_refresh` (bool): Force refresh cache even if not expired

**Returns:** Dict containing the JWKS

**Raises:** `ImproperlyConfigured` if JWKS cannot be fetched

**Caching:** Results are cached for 1 hour by default

```python
from oxutils.jwt.client import fetch_jwks

# Get cached JWKS
jwks = fetch_jwks()

# Force refresh
jwks = fetch_jwks(force_refresh=True)
```

---

#### `get_key(kid: str)`

Get the public key for a given Key ID.

**Parameters:**
- `kid` (str): The Key ID from JWT header

**Returns:** RSA public key for verification

**Raises:** `ValueError` if kid not found in JWKS

```python
from oxutils.jwt.client import get_key

try:
    key = get_key("main")
except ValueError as e:
    print(f"Key not found: {e}")
```

---

#### `verify_token(token: str) -> Dict[str, Any]`

Verify and decode a JWT token.

**Parameters:**
- `token` (str): The JWT token string to verify

**Returns:** Dict containing the decoded token payload

**Raises:**
- `jwt.InvalidTokenError`: If token is invalid or expired
- `ValueError`: If kid is not found

```python
from oxutils.jwt.client import verify_token
import jwt

try:
    payload = verify_token(token)
    print(f"User ID: {payload.get('sub')}")
    print(f"Expires: {payload.get('exp')}")
except jwt.ExpiredSignatureError:
    print("Token has expired")
except jwt.InvalidTokenError as e:
    print(f"Invalid token: {e}")
```

---

#### `clear_jwks_cache() -> None`

Clear the cached JWKS. Useful for testing or key rotation.

```python
from oxutils.jwt.client import clear_jwks_cache

# Clear cache to force refresh
clear_jwks_cache()
```

---

### Auth Module (`oxutils.jwt.auth`)

#### `get_jwks() -> Dict[str, Any]`

Get JSON Web Key Set for JWT verification from local key file.

**Returns:** Dict containing the public JWK in JWKS format

**Raises:** `ImproperlyConfigured` if key not configured or file doesn't exist

```python
from oxutils.jwt.auth import get_jwks

try:
    jwks = get_jwks()
    print(f"Keys: {len(jwks['keys'])}")
except ImproperlyConfigured as e:
    print(f"Configuration error: {e}")
```

---

#### `clear_jwk_cache() -> None`

Clear the cached JWK. Useful for testing or key rotation.

```python
from oxutils.jwt.auth import clear_jwk_cache

# Clear cache to reload key
clear_jwk_cache()
```

---

## Usage Examples

### Django Ninja Authentication

```python
# auth.py
from ninja.security import HttpBearer
from oxutils.jwt.client import verify_token
import jwt

class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = verify_token(token)
            request.jwt_payload = payload
            return payload
        except jwt.InvalidTokenError:
            return None

# api.py
from ninja import NinjaAPI
from .auth import JWTAuth

api = NinjaAPI(auth=JWTAuth())

@api.get("/protected")
def protected_endpoint(request):
    """Protected endpoint requiring JWT."""
    user_id = request.jwt_payload.get('sub')
    return {"message": f"Hello user {user_id}"}
```

### Django REST Framework Authentication

```python
# authentication.py
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from oxutils.jwt.client import verify_token
import jwt

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.replace('Bearer ', '')
        
        try:
            payload = verify_token(token)
            return (payload, None)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')

# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'myapp.authentication.JWTAuthentication',
    ],
}
```

### Middleware Authentication

```python
# middleware.py
from django.http import JsonResponse
from oxutils.jwt.client import verify_token
import jwt

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip authentication for public endpoints
        if request.path.startswith('/public/'):
            return self.get_response(request)
        
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse(
                {'error': 'Missing authentication token'},
                status=401
            )
        
        token = auth_header.replace('Bearer ', '')
        
        try:
            payload = verify_token(token)
            request.jwt_payload = payload
            request.user_id = payload.get('sub')
        except jwt.ExpiredSignatureError:
            return JsonResponse(
                {'error': 'Token has expired'},
                status=401
            )
        except jwt.InvalidTokenError:
            return JsonResponse(
                {'error': 'Invalid token'},
                status=401
            )
        
        return self.get_response(request)

# settings.py
MIDDLEWARE = [
    # ...
    'myapp.middleware.JWTAuthenticationMiddleware',
]
```

### Service-to-Service Authentication

```python
# services.py
import requests
from oxutils.jwt.client import verify_token

class ExternalServiceClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
    
    def call_api(self, endpoint: str, method: str = 'GET', data=None):
        """Make authenticated API call to external service."""
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()

# Usage
client = ExternalServiceClient(
    base_url='https://api.example.com',
    token='eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...'
)

result = client.call_api('/users/me')
```

### Token Extraction Utility

```python
# utils.py
from typing import Optional
from oxutils.jwt.client import verify_token
import jwt

def extract_token_from_request(request) -> Optional[str]:
    """Extract JWT token from request."""
    # Try Authorization header
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        return auth_header.replace('Bearer ', '')
    
    # Try query parameter
    token = request.GET.get('token')
    if token:
        return token
    
    # Try cookie
    token = request.COOKIES.get('access_token')
    if token:
        return token
    
    return None

def get_user_from_token(request) -> Optional[dict]:
    """Get user information from JWT token."""
    token = extract_token_from_request(request)
    
    if not token:
        return None
    
    try:
        payload = verify_token(token)
        return {
            'user_id': payload.get('sub'),
            'email': payload.get('email'),
            'roles': payload.get('roles', []),
            'org_id': payload.get('org_id'),
        }
    except jwt.InvalidTokenError:
        return None
```

---

## Integration Patterns

### Permission Checking

```python
# permissions.py
from functools import wraps
from django.http import JsonResponse
from oxutils.jwt.client import verify_token
import jwt

def require_jwt(required_roles=None):
    """Decorator to require JWT authentication with optional role checking."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            token = extract_token_from_request(request)
            
            if not token:
                return JsonResponse(
                    {'error': 'Authentication required'},
                    status=401
                )
            
            try:
                payload = verify_token(token)
                request.jwt_payload = payload
                
                # Check roles if required
                if required_roles:
                    user_roles = payload.get('roles', [])
                    if not any(role in user_roles for role in required_roles):
                        return JsonResponse(
                            {'error': 'Insufficient permissions'},
                            status=403
                        )
                
                return view_func(request, *args, **kwargs)
                
            except jwt.InvalidTokenError:
                return JsonResponse(
                    {'error': 'Invalid token'},
                    status=401
                )
        
        return wrapper
    return decorator

# Usage
@require_jwt(required_roles=['admin', 'manager'])
def admin_view(request):
    return JsonResponse({'message': 'Admin access granted'})
```

### Multi-Tenant Support

```python
# tenancy.py
from oxutils.jwt.client import verify_token

def get_tenant_from_token(request) -> Optional[str]:
    """Extract tenant/organization ID from JWT token."""
    token = extract_token_from_request(request)
    
    if not token:
        return None
    
    try:
        payload = verify_token(token)
        return payload.get('org_id') or payload.get('tenant_id')
    except jwt.InvalidTokenError:
        return None

class TenantMiddleware:
    """Middleware to set tenant context from JWT."""
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        tenant_id = get_tenant_from_token(request)
        if tenant_id:
            request.tenant_id = tenant_id
        
        return self.get_response(request)
```

### Token Refresh Pattern

```python
# refresh.py
import requests
from typing import Tuple

def refresh_access_token(refresh_token: str) -> Tuple[str, str]:
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_token: The refresh token
        
    Returns:
        Tuple of (new_access_token, new_refresh_token)
    """
    response = requests.post(
        'https://auth.example.com/token/refresh',
        json={'refresh_token': refresh_token}
    )
    response.raise_for_status()
    
    data = response.json()
    return data['access_token'], data['refresh_token']

# Automatic refresh middleware
class TokenRefreshMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        token = extract_token_from_request(request)
        
        if token:
            try:
                verify_token(token)
            except jwt.ExpiredSignatureError:
                # Try to refresh
                refresh_token = request.COOKIES.get('refresh_token')
                if refresh_token:
                    try:
                        new_access, new_refresh = refresh_access_token(refresh_token)
                        # Update tokens in response
                        response = self.get_response(request)
                        response.set_cookie('access_token', new_access)
                        response.set_cookie('refresh_token', new_refresh)
                        return response
                    except:
                        pass
        
        return self.get_response(request)
```

---

## Security Best Practices

### 1. Token Storage

**❌ Bad - Store in localStorage:**
```javascript
// Vulnerable to XSS attacks
localStorage.setItem('token', token);
```

**✅ Good - Use httpOnly cookies:**
```python
response.set_cookie(
    'access_token',
    token,
    httponly=True,
    secure=True,  # HTTPS only
    samesite='Strict'
)
```

### 2. Token Expiration

**Always set short expiration times:**

```python
# Token payload
payload = {
    'sub': user_id,
    'exp': datetime.utcnow() + timedelta(minutes=15),  # 15 minutes
    'iat': datetime.utcnow(),
}
```

### 3. Validate All Claims

```python
def validate_token_claims(payload: dict) -> bool:
    """Validate all required token claims."""
    required_claims = ['sub', 'exp', 'iat']
    
    # Check required claims exist
    if not all(claim in payload for claim in required_claims):
        return False
    
    # Validate expiration
    exp = payload.get('exp')
    if datetime.fromtimestamp(exp) < datetime.utcnow():
        return False
    
    # Validate issuer if configured
    expected_issuer = 'https://auth.example.com'
    if payload.get('iss') != expected_issuer:
        return False
    
    return True
```

### 4. Key Rotation

```python
# Implement key rotation
from oxutils.jwt.client import clear_jwks_cache

def rotate_keys():
    """Rotate JWT keys."""
    # Clear cache to fetch new keys
    clear_jwks_cache()
    
    # Verify new keys work
    try:
        fetch_jwks(force_refresh=True)
        logger.info("Key rotation successful")
    except Exception as e:
        logger.error("Key rotation failed", error=str(e))
        raise
```

### 5. Rate Limiting

```python
from django.core.cache import cache

def rate_limit_token_verification(token: str) -> bool:
    """Rate limit token verification attempts."""
    cache_key = f"token_verify:{token[:10]}"
    attempts = cache.get(cache_key, 0)
    
    if attempts >= 5:
        return False
    
    cache.set(cache_key, attempts + 1, timeout=60)
    return True
```

### 6. Audit Logging

```python
import structlog

logger = structlog.get_logger(__name__)

def verify_token_with_audit(token: str, request):
    """Verify token with audit logging."""
    try:
        payload = verify_token(token)
        
        logger.info(
            "token_verified",
            user_id=payload.get('sub'),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        return payload
        
    except jwt.InvalidTokenError as e:
        logger.warning(
            "token_verification_failed",
            error=str(e),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        raise
```

---

## Troubleshooting

### Common Issues

#### 1. "JWT verifying key is not configured"

**Cause:** Missing configuration

**Solution:**
```bash
export OXI_JWT_VERIFYING_KEY="/path/to/public_key.pem"
# OR
export OXI_JWT_JWKS_URL="https://auth.example.com/.well-known/jwks.json"
```

#### 2. "Token header missing 'kid' field"

**Cause:** Token doesn't include Key ID

**Solution:** Ensure tokens include `kid` in header:
```python
headers = {
    'kid': 'main',
    'alg': 'RS256',
    'typ': 'JWT'
}
```

#### 3. "Unknown Key ID (kid)"

**Cause:** Key ID not found in JWKS

**Solution:** Clear cache and refresh:
```python
from oxutils.jwt.client import clear_jwks_cache, fetch_jwks

clear_jwks_cache()
jwks = fetch_jwks(force_refresh=True)
```

#### 4. Token Expired

**Cause:** Token past expiration time

**Solution:** Implement token refresh:
```python
try:
    payload = verify_token(token)
except jwt.ExpiredSignatureError:
    # Refresh token logic
    new_token = refresh_access_token(refresh_token)
```

#### 5. JWKS Fetch Timeout

**Cause:** Authentication server unreachable

**Solution:** Implement fallback:
```python
try:
    jwks = fetch_jwks()
except ImproperlyConfigured:
    # Use cached keys or local keys as fallback
    from oxutils.jwt.auth import get_jwks
    jwks = get_jwks()
```

### Debugging

**Enable debug logging:**

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('oxutils.jwt')
logger.setLevel(logging.DEBUG)
```

**Inspect token without verification:**

```python
import jwt

# Decode without verification (for debugging only!)
headers = jwt.get_unverified_header(token)
payload = jwt.decode(token, options={"verify_signature": False})

print(f"Headers: {headers}")
print(f"Payload: {payload}")
```

**Test JWKS endpoint:**

```bash
curl -X GET https://auth.example.com/.well-known/jwks.json
```

---

## Testing

### Unit Tests

```python
# tests/test_jwt.py
import pytest
from oxutils.jwt.client import verify_token, clear_jwks_cache
from oxutils.jwt.auth import get_jwks, clear_jwk_cache
import jwt

@pytest.fixture(autouse=True)
def clear_caches():
    """Clear caches before each test."""
    clear_jwks_cache()
    clear_jwk_cache()

def test_verify_valid_token(valid_token):
    """Test verification of valid token."""
    payload = verify_token(valid_token)
    assert 'sub' in payload
    assert 'exp' in payload

def test_verify_expired_token(expired_token):
    """Test verification of expired token."""
    with pytest.raises(jwt.ExpiredSignatureError):
        verify_token(expired_token)

def test_verify_invalid_signature(invalid_token):
    """Test verification of token with invalid signature."""
    with pytest.raises(jwt.InvalidSignatureError):
        verify_token(invalid_token)

def test_jwks_caching():
    """Test JWKS caching mechanism."""
    from oxutils.jwt.client import fetch_jwks, _jwks_cache
    
    # First fetch
    jwks1 = fetch_jwks()
    
    # Second fetch should use cache
    jwks2 = fetch_jwks()
    
    assert jwks1 == jwks2
    assert _jwks_cache is not None
```

### Integration Tests

```python
# tests/test_integration.py
from django.test import TestCase, Client
from oxutils.jwt.client import verify_token

class JWTAuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.token = generate_test_token()
    
    def test_authenticated_request(self):
        """Test authenticated API request."""
        response = self.client.get(
            '/api/protected',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_unauthenticated_request(self):
        """Test request without token."""
        response = self.client.get('/api/protected')
        self.assertEqual(response.status_code, 401)
```

---

## Related Documentation

- [Settings & Configuration](./settings.md) - JWT configuration options
- [Exceptions & Utilities](./misc.md) - Authentication exceptions
- [Celery Integration](./celery.md) - JWT in async tasks

---

## Support

For questions or issues regarding JWT authentication, please contact the Oxiliere development team or open an issue in the repository.
