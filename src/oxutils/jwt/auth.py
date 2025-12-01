import os
from typing import Dict, Any, Optional
from jwcrypto import jwk
from django.core.exceptions import ImproperlyConfigured
from oxutils.settings import oxi_settings



_public_jwk_cache: Optional[jwk.JWK] = None



def get_jwks() -> Dict[str, Any]:
    """
    Get JSON Web Key Set (JWKS) for JWT verification.
    
    Returns:
        Dict containing the public JWK in JWKS format.
        
    Raises:
        ImproperlyConfigured: If jwt_verifying_key is not configured or file doesn't exist.
    """
    global _public_jwk_cache
    
    if oxi_settings.jwt_verifying_key is None:
        raise ImproperlyConfigured(
            "JWT verifying key is not configured. Set OXI_JWT_VERIFYING_KEY environment variable."
        )
    
    key_path = oxi_settings.jwt_verifying_key
    
    if not os.path.exists(key_path):
        raise ImproperlyConfigured(
            f"JWT verifying key file not found at: {key_path}"
        )
    
    if _public_jwk_cache is None:
        try:
            with open(key_path, 'r') as f:
                key_data = f.read()
            
            _public_jwk_cache = jwk.JWK.from_pem(key_data.encode('utf-8'))
            _public_jwk_cache.update(kid='main')
        except Exception as e:
            raise ImproperlyConfigured(
                f"Failed to load JWT verifying key from {key_path}: {str(e)}"
            )
    
    return {"keys": [_public_jwk_cache.export(as_dict=True)]}


def clear_jwk_cache() -> None:
    """Clear the cached JWK. Useful for testing or key rotation."""
    global _public_jwk_cache
    _public_jwk_cache = None
