# JWT Security Best Practices

## Overview

This document outlines the security features and best practices for using JWT authentication in OxUtils.

## Security Features

### 1. Token Blacklisting

Tokens can be revoked before expiration using the JTI (JWT ID) claim:

```python
from oxutils.jwt.utils import blacklist_token
from ninja_jwt.tokens import AccessToken

# Blacklist a token (e.g., on logout)
token = AccessToken(raw_token)
blacklist_token(token, reason="user_logout")
```

**How it works:**
- Tokens must include a `jti` claim (JWT ID)
- Blacklisted tokens are stored in cache with TTL matching token expiration
- Middleware automatically checks blacklist on each request

### 2. Rate Limiting

Built-in rate limiting protects against brute force attacks:

- **Limit**: 10 failed authentication attempts per minute per IP
- **Scope**: Per IP address (supports proxy headers)
- **Reset**: Counter resets on successful authentication

**Configuration:**

Rate limiting is automatic. To customize:

```python
# In your middleware subclass
class CustomJWTMiddleware(JWTAuthBaseMiddleware):
    def process_request(self, request):
        # Customize rate limit
        rate_limit_key = f'jwt_auth_attempts:{ip_address}'
        max_attempts = 5  # Custom limit
        window = 300  # 5 minutes
```

### 3. Token Validation

Multiple layers of validation:

1. **Format validation**: JWT must have 3 parts (header.payload.signature)
2. **Signature verification**: Cryptographic signature check
3. **Expiration check**: Token must not be expired
4. **Blacklist check**: Token must not be revoked
5. **User ID validation**: 
   - Must be present in token
   - Must be int or string
   - String max length: 255 characters
6. **User status check**: User must be active (for DB-backed auth)

### 4. Secure Logging

Security events are logged without exposing sensitive data:

```python
# ✅ Good - logs IP and error type
logger.warning(
    f"Invalid JWT token from {ip_address}: InvalidToken",
    extra={'path': request.path, 'ip': ip_address}
)

# ❌ Bad - never log the actual token
logger.error(f"Invalid token: {token}")  # NEVER DO THIS
```

**Logged events:**
- Invalid token format
- Authentication failures
- Rate limit exceeded
- Blacklisted token attempts

### 5. IP Address Detection

Supports proxy headers for accurate IP detection:

```python
# Checks in order:
# 1. HTTP_X_FORWARDED_FOR (first IP in chain)
# 2. REMOTE_ADDR
```

## Middleware Options

### JWTHeaderAuthMiddleware (Recommended)

Stateless authentication from Authorization header:

```python
# settings.py
MIDDLEWARE = [
    # ...
    'oxutils.jwt.middleware.JWTHeaderAuthMiddleware',
    # ...
]
```

**Features:**
- Stateless (no DB lookup)
- Rate limiting
- Token blacklisting
- Secure logging

### JWTCookieAuthMiddleware

Stateless authentication from cookies:

```python
# settings.py
MIDDLEWARE = [
    # ...
    'oxutils.jwt.middleware.JWTCookieAuthMiddleware',
    # ...
]
```

**Cookie requirements:**
```python
# settings.py
SESSION_COOKIE_SECURE = True      # HTTPS only
SESSION_COOKIE_HTTPONLY = True    # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Strict'  # CSRF protection
```

## Configuration

### Required Settings

```python
# settings.py
from datetime import timedelta

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    
    # Security
    'ALGORITHM': 'RS256',  # Use asymmetric encryption
    'SIGNING_KEY': settings.SECRET_KEY,
    'VERIFYING_KEY': None,
    
    # Include JTI for blacklisting
    'JTI_CLAIM': 'jti',
    
    # User identification
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# Cache (required for blacklisting and rate limiting)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Cookie Configuration

```python
# settings.py
from oxutils.constants import ACCESS_TOKEN_COOKIE

# Cookie settings
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_AGE = 900  # 15 minutes

# Custom cookie name (optional)
# Default is 'access_token' from ACCESS_TOKEN_COOKIE
```

## Usage Examples

### User Logout (Blacklist Token)

```python
from ninja import Router
from ninja_jwt.tokens import AccessToken
from oxutils.jwt.utils import blacklist_token

router = Router()

@router.post("/logout")
def logout(request):
    # Get token from request
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        raw_token = auth_header[7:]
        token = AccessToken(raw_token)
        blacklist_token(token, reason="user_logout")
    
    return {"message": "Logged out successfully"}
```

### Password Reset (Invalidate All Tokens)

```python
from oxutils.jwt.utils import clear_user_tokens

def reset_password(user, new_password):
    user.set_password(new_password)
    user.save()
    
    # Clear rate limits (optional)
    clear_user_tokens(user.id)
    
    # Note: To invalidate all existing tokens, you need to:
    # 1. Track active tokens per user (custom implementation)
    # 2. Blacklist them all
    # OR
    # 3. Change user's password salt/secret (forces re-authentication)
```

### Custom Rate Limiting

```python
from oxutils.jwt.middleware import JWTHeaderAuthMiddleware

class StrictJWTMiddleware(JWTHeaderAuthMiddleware):
    """Custom middleware with stricter rate limiting."""
    
    def process_request(self, request):
        # Custom rate limit for specific paths
        if request.path.startswith('/api/admin/'):
            ip_address = self._get_client_ip(request)
            rate_limit_key = f'jwt_admin_attempts:{ip_address}'
            attempts = cache.get(rate_limit_key, 0)
            
            # Stricter limit for admin endpoints
            if attempts >= 3:
                logger.warning(f"Admin rate limit exceeded for {ip_address}")
                request.user = AnonymousUser()
                return
        
        # Call parent implementation
        super().process_request(request)
```

## Security Checklist

### Production Deployment

- [ ] Use HTTPS only (`SESSION_COOKIE_SECURE = True`)
- [ ] Set `HttpOnly` cookies (`SESSION_COOKIE_HTTPONLY = True`)
- [ ] Configure `SameSite` (`SESSION_COOKIE_SAMESITE = 'Strict'`)
- [ ] Use Redis for cache backend (not in-memory)
- [ ] Configure proper CORS settings
- [ ] Use asymmetric encryption (RS256) for tokens
- [ ] Set short token lifetimes (15 min for access, 1 day for refresh)
- [ ] Enable token rotation
- [ ] Monitor failed authentication attempts
- [ ] Set up security alerts for rate limit violations

### Code Review

- [ ] Never log tokens or sensitive data
- [ ] Always validate user input
- [ ] Use parameterized queries (ORM handles this)
- [ ] Implement proper error handling
- [ ] Don't expose internal error details to clients
- [ ] Use environment variables for secrets
- [ ] Rotate secrets regularly

## Monitoring

### Key Metrics to Track

1. **Failed authentication rate**
   - Alert if > 100 failures/minute
   
2. **Rate limit violations**
   - Track IPs hitting rate limits
   
3. **Blacklisted token attempts**
   - May indicate token theft
   
4. **Token validation errors**
   - Spike may indicate attack

### Log Analysis

```python
# Example: Find IPs with most failed attempts
grep "JWT authentication failed" /var/log/django.log | \
  awk '{print $NF}' | sort | uniq -c | sort -rn | head -10
```

## Troubleshooting

### "Token has been revoked"

**Cause**: Token is blacklisted
**Solution**: User needs to re-authenticate

### "Rate limit exceeded"

**Cause**: Too many failed attempts from IP
**Solution**: Wait 1 minute or contact admin

### "Invalid user identification format"

**Cause**: Token contains invalid user_id claim
**Solution**: Token may be tampered, re-authenticate

### "User not found"

**Cause**: User deleted or user_id invalid
**Solution**: Re-authenticate or check user status

## Related Documentation

- [JWT Authentication](jwt.md)
- [Settings](settings.md)
- [Audit System](audit.md)
