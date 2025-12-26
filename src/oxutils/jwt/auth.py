import os
from typing import Dict, Any, Optional, Type
from django.utils.translation import gettext_lazy as _
from django.http import HttpRequest
from django.contrib.auth.models import AbstractUser
from jwcrypto import jwk
from django.core.exceptions import ImproperlyConfigured

from ninja_jwt.authentication import (
    JWTBaseAuthentication,
    JWTStatelessUserAuthentication
)
from ninja.security import (
    APIKeyCookie,
)
from ninja_jwt.exceptions import InvalidToken
from ninja_jwt.settings import api_settings
from oxutils.constants import ACCESS_TOKEN_COOKIE
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


class AuthMixin:
    def jwt_authenticate(self, request: HttpRequest, token: str) -> AbstractUser:
        """
        Add token_user to the request object, witch will be erased by the jwt_allauth.utils.popolate_user
        function.
        """
        token_user = super().jwt_authenticate(request, token)
        request.token_user = token_user
        return token_user



class JWTAuth(AuthMixin, JWTStatelessUserAuthentication):
    pass


class JWTCookieAuth(AuthMixin, JWTBaseAuthentication, APIKeyCookie):
    """
    An authentication plugin that authenticates requests through a JSON web
    token provided in a request header without performing a database lookup to obtain a user instance.
    """

    param_name = ACCESS_TOKEN_COOKIE

    def authenticate(self, request: HttpRequest, token: str) -> Any:
        return self.jwt_authenticate(request, token)

    def get_user(self, validated_token: Any) -> Type[AbstractUser]:
        """
        Returns a stateless user object which is backed by the given validated
        token.
        """
        if api_settings.USER_ID_CLAIM not in validated_token:
            # The TokenUser class assumes tokens will have a recognizable user
            # identifier claim.
            raise InvalidToken(_("Token contained no recognizable user identification"))

        return api_settings.TOKEN_USER_CLASS(validated_token)


jwt_auth = JWTAuth()
jwt_cookie_auth = JWTCookieAuth()
