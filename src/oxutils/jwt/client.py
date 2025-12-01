import jwt
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.core.exceptions import ImproperlyConfigured
from oxutils.settings import oxi_settings
from .constants import JWT_ALGORITHM


_jwks_cache: Optional[Dict[str, Any]] = None
_jwks_cache_time: Optional[datetime] = None
_jwks_cache_ttl = timedelta(hours=1)


def get_jwks_url() -> str:
    """
    Get JWKS URL from settings.
    
    Returns:
        The configured JWKS URL.
        
    Raises:
        ImproperlyConfigured: If jwt_jwks_url is not configured.
    """
    if not oxi_settings.jwt_jwks_url:
        raise ImproperlyConfigured(
            "JWT JWKS URL is not configured. Set OXI_JWT_JWKS_URL environment variable."
        )
    return oxi_settings.jwt_jwks_url


def fetch_jwks(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Fetch JWKS from the authentication server with caching.
    
    Args:
        force_refresh: Force refresh the cache even if not expired.
        
    Returns:
        Dict containing the JWKS.
        
    Raises:
        ImproperlyConfigured: If JWKS cannot be fetched.
    """
    global _jwks_cache, _jwks_cache_time
    
    now = datetime.now()
    
    # Return cached JWKS if valid
    if not force_refresh and _jwks_cache is not None and _jwks_cache_time is not None:
        if now - _jwks_cache_time < _jwks_cache_ttl:
            return _jwks_cache
    
    # Fetch fresh JWKS
    jwks_url = get_jwks_url()
    try:
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_cache_time = now
        return _jwks_cache
    except requests.RequestException as e:
        raise ImproperlyConfigured(
            f"Failed to fetch JWKS from {jwks_url}: {str(e)}"
        )


def get_key(kid: str):
    """
    Get the public key for a given Key ID (kid).
    
    Args:
        kid: The Key ID from the JWT header.
        
    Returns:
        RSA public key for verification.
        
    Raises:
        ValueError: If the kid is not found in JWKS.
    """
    jwks = fetch_jwks()
    
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)
    
    raise ValueError(f"Unknown Key ID (kid): {kid}")


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token string to verify.
        
    Returns:
        Dict containing the decoded token payload.
        
    Raises:
        jwt.InvalidTokenError: If token is invalid or expired.
        ValueError: If kid is not found.
    """
    try:
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")
        
        if not kid:
            raise ValueError("Token header missing 'kid' field")
        
        key = get_key(kid)
        return jwt.decode(token, key=key, algorithms=JWT_ALGORITHM)
    except jwt.InvalidTokenError:
        raise
    except Exception as e:
        raise jwt.InvalidTokenError(f"Token verification failed: {str(e)}")


def clear_jwks_cache() -> None:
    """Clear the cached JWKS. Useful for testing or key rotation."""
    global _jwks_cache, _jwks_cache_time
    _jwks_cache = None
    _jwks_cache_time = None
