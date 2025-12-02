# JWT Authentication

**RS256 with JWKS support and automatic caching**

## Features

- RS256 algorithm (RSA public/private keys)
- JWKS fetching with 1-hour cache
- Token verification and validation
- Django Ninja integration

## Configuration

```bash
# JWKS-based (recommended)
OXI_JWT_JWKS_URL=https://auth.example.com/.well-known/jwks.json

# Local keys
OXI_JWT_VERIFYING_KEY=/path/to/public_key.pem
OXI_JWT_SIGNING_KEY=/path/to/private_key.pem
```

## Usage

### Basic Verification

```python
from oxutils.jwt.client import verify_token
import jwt

try:
    payload = verify_token(token)
    user_id = payload.get('sub')
except jwt.InvalidTokenError:
    pass
```

### Django Ninja Integration

```python
from ninja import NinjaAPI
from ninja.security import HttpBearer
from oxutils.jwt.client import verify_token

class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            return verify_token(token)
        except:
            return None

api = NinjaAPI(auth=JWTAuth())

@api.get("/protected")
def protected(request):
    return {"user_id": request.auth['sub']}
```

## API Reference

### `verify_token(token: str) -> dict`

Verify and decode JWT token.

**Returns:** Token payload  
**Raises:** `jwt.InvalidTokenError` if invalid

### `fetch_jwks(force_refresh: bool = False) -> dict`

Fetch JWKS from auth server (cached 1 hour).

### `clear_jwks_cache()`

Clear JWKS cache (useful for key rotation).

## Generate Keys

```bash
# Generate private key
openssl genrsa -out private_key.pem 2048

# Extract public key
openssl rsa -in private_key.pem -pubout -out public_key.pem
```

## Related Docs

- [Settings](./settings.md) - JWT configuration
- [Exceptions](./misc.md) - Error handling
