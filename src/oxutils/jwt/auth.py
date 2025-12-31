import os
from typing import Dict, Any, Optional, Type, Tuple, List
from django.utils.translation import gettext_lazy as _
from django.http import HttpRequest
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import (
    authenticate as django_authenticate,
    login as django_login,
    get_user_model
)
from jwcrypto import jwk
from django.core.exceptions import ImproperlyConfigured

from ninja.security.base import AuthBase
from ninja_jwt.authentication import (
    JWTBaseAuthentication,
    JWTStatelessUserAuthentication
)
from ninja.security import (
    APIKeyCookie,
    HttpBasicAuth,
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


def authenticate_by_x_session_token(token: str) -> Optional[Tuple]:
    """
    Copied from allauth.headless.internal.sessionkit, to "select_related"
    """
    from allauth.headless import app_settings


    session = app_settings.TOKEN_STRATEGY.lookup_session(token)
    if not session:
        return None
    user_id_str = session.get(SESSION_KEY)
    if user_id_str:
        meta_pk = get_user_model()._meta.pk
        if meta_pk:
            user_id = meta_pk.to_python(user_id_str)
            user = get_user_model().objects.filter(pk=user_id).first()
            if user and user.is_active:
                return (user, session)
    return None


class XSessionTokenAuth(AuthBase):
    """
    This security class uses the X-Session-Token that django-allauth
    is using for authentication purposes.
    """

    openapi_type: str = "apiKey"

    def __call__(self, request: HttpRequest):
        token = self.get_session_token(request)
        if token:
            user_session = authenticate_by_x_session_token(token)
            if user_session:
                return user_session[0]
        return None

    def get_session_token(self, request: HttpRequest) -> Optional[str]:
        """
        Returns the session token for the given request, by looking up the
        ``X-Session-Token`` header. Override this if you want to extract the token
        from e.g. the ``Authorization`` header.
        """
        if request.session.session_key:
            return request.session.session_key
        
        return request.headers.get("X-Session-Token")


class BasicAuth(HttpBasicAuth):
    def authenticate(self, request: HttpRequest, username: str, password: str) -> Optional[Any]:
        user = django_authenticate(email=username, password=password)
        if user and user.is_active:
            django_login(request, user)
            return user
        return None


class BasicNoPasswordAuth(HttpBasicAuth):
    def authenticate(self, request: HttpRequest, username: str, password: str) -> Optional[Any]:
        try:
            user = get_user_model().objects.get(email=username)
            if user and user.is_active:
                django_login(request, user)
                return user
            return None
        except Exception as e:
            return None

x_session_token_auth = XSessionTokenAuth()
basic_auth = BasicAuth()
basic_no_password_auth = BasicNoPasswordAuth()
jwt_auth = JWTAuth()
jwt_cookie_auth = JWTCookieAuth()




def get_auth_handlers(auths: List[AuthBase] = []) -> List[AuthBase]:
    """Auth handler switcher based on settings.DEBUG"""
    from django.conf import settings

    if settings.DEBUG:
        return auths

    return [jwt_auth, jwt_cookie_auth]
