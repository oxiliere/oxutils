# JWT Authentication

**Stateless JWT authentication with ninja-jwt and custom token types**

## Features

- Stateless JWT authentication (no database lookup)
- RS256 algorithm (RSA public/private keys)
- JWKS generation from PEM files with caching
- Multiple token types (Access, Service, Organization)
- Django Ninja integration with Bearer and Cookie auth
- Custom TokenUser and TokenTenant models
- User population decorator for full user loading

## Configuration

### Environment Variables

#### JWT Keys

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OXI_JWT_SIGNING_KEY` | string | `None` | Path to RSA private key (PEM) for signing tokens. Required for token generation. |
| `OXI_JWT_VERIFYING_KEY` | string | `None` | Path to RSA public key (PEM) for verifying tokens. Required for authentication. |
| `OXI_JWT_JWKS_URL` | string | `None` | Remote JWKS URL (optional, used by ninja-jwt). |
| `OXI_JWT_ALGORITHM` | string | `'RS256'` | JWT signing algorithm. |

#### Token Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OXI_JWT_ACCESS_TOKEN_KEY` | string | `'access'` | Token type for user access tokens. |
| `OXI_JWT_SERVICE_TOKEN_KEY` | string | `'service'` | Token type for service tokens. |
| `OXI_JWT_ORG_ACCESS_TOKEN_KEY` | string | `'org_access'` | Token type for organization/tenant tokens. |

#### Token Lifetime

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OXI_JWT_ACCESS_TOKEN_LIFETIME` | int | `15` | Access token lifetime in minutes. |
| `OXI_JWT_SERVICE_TOKEN_LIFETIME` | int | `3` | Service token lifetime in minutes. |
| `OXI_JWT_ORG_ACCESS_TOKEN_LIFETIME` | int | `60` | Organization token lifetime in minutes. |

### Example Configuration

```bash
# JWT Keys
OXI_JWT_SIGNING_KEY=/path/to/keys/private_key.pem
OXI_JWT_VERIFYING_KEY=/path/to/keys/public_key.pem
OXI_JWT_ALGORITHM=RS256

# Token types
OXI_JWT_ACCESS_TOKEN_KEY=access
OXI_JWT_SERVICE_TOKEN_KEY=service
OXI_JWT_ORG_ACCESS_TOKEN_KEY=org_access

# Token lifetimes (in minutes)
OXI_JWT_ACCESS_TOKEN_LIFETIME=15
OXI_JWT_SERVICE_TOKEN_LIFETIME=3
OXI_JWT_ORG_ACCESS_TOKEN_LIFETIME=60
```

## Token Types

### AccessToken

Standard token for user authentication (ninja-jwt).

```python
from ninja_jwt.tokens import AccessToken

token = AccessToken.for_user(user)
print(token)  # eyJ0eXAiOiJKV1QiLCJhbGc...
```

### OxilierServiceToken

Token for inter-service authentication.

```python
from oxutils.jwt.tokens import OxilierServiceToken

token = OxilierServiceToken.for_service({
    'service_name': 'my-service',
    'permissions': ['read', 'write']
})
```

### OrganizationAccessToken

Token for tenant/organization authentication (multitenancy).

```python
from oxutils.jwt.tokens import OrganizationAccessToken

token = OrganizationAccessToken.for_tenant(tenant)
# Includes: tenant_id, oxi_id, schema_name, subscription info, status
```

## Authentication Classes

### JWTAuth (Bearer Token)

Authentication via `Authorization: Bearer <token>` header.

```python
from ninja import NinjaAPI
from oxutils.jwt.auth import jwt_auth

api = NinjaAPI(auth=jwt_auth)

@api.get("/protected")
def protected(request):
    # request.user is a TokenUser instance
    return {"user_id": str(request.user.id)}
```

### JWTCookieAuth (Cookie)

Authentication via cookie (name: `ACCESS_TOKEN_COOKIE`).

```python
from ninja import NinjaAPI
from oxutils.jwt.auth import jwt_cookie_auth

api = NinjaAPI(auth=jwt_cookie_auth)

@api.get("/protected")
def protected(request):
    return {"user_id": str(request.user.id)}
```

## Models

### TokenUser

Stateless user based on JWT token (no database lookup).

```python
from oxutils.jwt.models import TokenUser

# Automatically created by authentication
# request.user is a TokenUser instance

# Properties
user.id  # UUID from token
user.token_created_at  # Token creation timestamp
user.token_session  # Session identifier
```

### TokenTenant

Stateless tenant based on organization token.

```python
from oxutils.jwt.models import TokenTenant

tenant = TokenTenant.for_token(org_token)
print(tenant.schema_name)
print(tenant.oxi_id)
print(tenant.subscription_plan)
```

## User Population

To load the full user from the database (when necessary):

### Decorator

```python
from oxutils.jwt.utils import load_user

class MyAPI:
    @load_user
    def my_view(self, request):
        # request.user is now the full User model instance
        return {"email": request.user.email}
```

### Manual

```python
from oxutils.jwt.utils import populate_user

def my_view(request):
    populate_user(request)
    # request.user is now the full User model instance
    return {"email": request.user.email}
```

## JWKS Generation

The system automatically generates JWKS from the public key PEM file.

```python
from oxutils.jwt.auth import get_jwks, clear_jwk_cache

# Get JWKS (cached)
jwks = get_jwks()
# Returns: {"keys": [{"kty": "RSA", "kid": "main", ...}]}

# Clear cache (key rotation)
clear_jwk_cache()
```

## Usage Examples

### Protected Endpoint

```python
from ninja import NinjaAPI
from oxutils.jwt.auth import jwt_auth

api = NinjaAPI(auth=jwt_auth)

@api.get("/users/me")
def get_current_user(request):
    return {
        "id": str(request.user.id),
        "token_created_at": request.user.token_created_at,
        "session": request.user.token_session
    }
```

### With User Loading

```python
from ninja import NinjaAPI, Router
from oxutils.jwt.auth import jwt_auth
from oxutils.jwt.utils import load_user

router = Router(auth=jwt_auth)

@router.get("/profile")
@load_user
def get_profile(request):
    # request.user is the full User model
    return {
        "email": request.user.email,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name
    }
```

### Service Token

```python
from oxutils.jwt.tokens import OxilierServiceToken

# Create service token
token = OxilierServiceToken.for_service({
    'service': 'payment-service',
    'action': 'process_payment'
})

# Use in requests
headers = {'Authorization': f'Bearer {token}'}
```

### Organization Token

```python
from oxutils.jwt.tokens import OrganizationAccessToken
from oxutils.jwt.models import TokenTenant

# Create org token
token = OrganizationAccessToken.for_tenant(tenant)

# Parse org token
tenant = TokenTenant.for_token(str(token))
print(f"Tenant: {tenant.schema_name}")
print(f"Plan: {tenant.subscription_plan}")
```

## Generate RSA Keys

```bash
# Generate private key (2048 bits)
openssl genrsa -out private_key.pem 2048

# Extract public key
openssl rsa -in private_key.pem -pubout -out public_key.pem

# Verify keys
openssl rsa -in private_key.pem -check
openssl rsa -pubin -in public_key.pem -text -noout
```

## Error Handling

```python
from ninja_jwt.exceptions import InvalidToken
from django.core.exceptions import ImproperlyConfigured

try:
    # Authentication happens automatically
    pass
except InvalidToken:
    # Token is invalid, expired, or malformed
    return {"error": "Invalid token"}
except ImproperlyConfigured:
    # JWT keys not configured properly
    return {"error": "Server configuration error"}
```

## Best Practices

1. **Use stateless auth by default**: Avoid DB lookups unless necessary
2. **Load user only when needed**: Use `@load_user` decorator sparingly
3. **Rotate keys regularly**: Use `clear_jwk_cache()` after key rotation
4. **Set appropriate lifetimes**: Short for access tokens, very short for service tokens
5. **Secure keys**: Never commit keys to version control
6. **Use environment variables**: Configure all JWT settings via `OXI_` env vars

## Related Docs

- [Settings](./settings.md) - Complete JWT configuration
