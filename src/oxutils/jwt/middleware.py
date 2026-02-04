from typing import Type, Optional
import structlog

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from ninja_jwt.exceptions import AuthenticationFailed, InvalidToken, TokenError
from ninja_jwt.settings import api_settings
from ninja_jwt.tokens import Token
from oxutils.constants import ACCESS_TOKEN_COOKIE
from ninja.utils import check_csrf


logger = structlog.get_logger(__name__)




class JWTAuthBaseMiddleware:
    """
    Base middleware for JWT authentication.
    Handles token validation and user authentication.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.user_model = get_user_model()

    def __call__(self, request: HttpRequest):
        """
        Process the request through the middleware.
        """
        # Process request before view
        self.process_request(request)
        
        # Get response from next middleware/view
        response = self.get_response(request)
        
        return response

    def get_token_from_request(self, request: HttpRequest) -> Optional[str]:
        """
        Extract JWT token from request.
        Must be implemented by subclasses.
        
        Returns:
            Token string if found, None otherwise
        """
        raise NotImplementedError(
            "Subclasses must implement get_token_from_request() method"
        )
    
    def process_request(self, request: HttpRequest):
        """
        Process request and validate JWT token if present.
        Authentication is handled by another service - this only validates token signature and claims.
        
        Skips authentication if user is already authenticated by a previous middleware.
        """
        # Skip if user is already authenticated by another middleware
        if hasattr(request, 'user') and request.user.is_authenticated:
            if settings.DEBUG:
                logger.debug(
                    "jwt_auth_skipped",
                    description="User already authenticated, skipping JWT middleware",
                    user_id=getattr(request.user, 'id', None),
                    path=request.path
                )
            return
        
        try:
            token = self.get_token_from_request(request)
        except PermissionDenied as e:
            # CSRF or other security check failed
            logger.warning(
                "security_check_failed",
                description="Security check failed during token extraction",
                exception=type(e).__name__,
                error=str(e),
                path=request.path,
                remote_addr=request.META.get('REMOTE_ADDR')
            )
            request.user = AnonymousUser()
            return
        
        if token:
            try:
                # Only validate token and extract user info (no DB lookup)
                self.jwt_authenticate(request, token)
            except (InvalidToken, AuthenticationFailed) as e:
                # Token invalid - set anonymous user
                if settings.DEBUG:
                    logger.debug(
                        "jwt_validation_failed",
                        description="JWT validation failed",
                        exception=type(e).__name__,
                        path=request.path
                    )
                request.user = AnonymousUser()
        else:
            # No token provided - anonymous user
            request.user = AnonymousUser()

    @classmethod
    def get_validated_token(cls, raw_token) -> Type[Token]:
        """
        Validates an encoded JSON web token and returns a validated token wrapper object.
        Only validates signature and claims - authentication is handled by external service.
        """
        messages = []
        for AuthToken in api_settings.AUTH_TOKEN_CLASSES:
            try:
                return AuthToken(raw_token)
            except TokenError as e:
                messages.append(
                    {
                        "token_class": AuthToken.__name__,
                        "token_type": AuthToken.token_type,
                        "message": e.args[0],
                    }
                )

        raise InvalidToken(
            {
                "detail": _("Given token not valid for any token type"),
                "messages": messages,
            }
        )

    def get_user(self, validated_token) -> AbstractBaseUser:
        """
        Returns a stateless user object from the validated token.
        No database lookup - authentication is handled by external service.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError as e:
            raise InvalidToken(
                _("Token contained no recognizable user identification")
            ) from e

        # Validate user_id type and value
        if not isinstance(user_id, (int, str)) or not user_id:
            raise InvalidToken(_("Invalid user identification format"))
        
        # Additional validation for string user_id
        if isinstance(user_id, str) and len(user_id) > 255:
            raise InvalidToken(_("User identification too long"))

        # Return stateless TokenUser (no DB lookup)
        return api_settings.TOKEN_USER_CLASS(validated_token)

    def jwt_authenticate(self, request: HttpRequest, token: str) -> AbstractBaseUser:
        """
        Authenticate user from JWT token and attach to request.
        """
        validated_token = self.get_validated_token(token)
        user = self.get_user(validated_token)
        request.user = user
        request.token_user = user # For backward compatibility and request.user can be overridden by other middlewares
        return user
    

class JWTHeaderAuthMiddleware(JWTAuthBaseMiddleware):
    """
    JWT authentication middleware that extracts token from Authorization header.
    Stateless authentication without database lookup.
    """
    openapi_scheme: str = "bearer"
    header: str = "Authorization"


    def get_token_from_request(self, request: HttpRequest) -> str:
        """
        Extract JWT token from Authorization header.
        Validates scheme and format without logging sensitive data.
        """
        headers = request.headers
        auth_value = headers.get(self.header)
        if not auth_value:
            return None
        
        parts = auth_value.split(" ")
        
        # Validate minimum parts
        if len(parts) < 2:
            if settings.DEBUG:
                logger.warning(
                    "invalid_authorization_header",
                    description="Invalid Authorization header format",
                    remote_addr=request.META.get('REMOTE_ADDR')
                )
            return None

        # Validate scheme
        if parts[0].lower() != self.openapi_scheme:
            if settings.DEBUG:
                logger.warning(
                    "unexpected_auth_scheme",
                    description="Unexpected auth scheme",
                    expected_scheme=self.openapi_scheme,
                    actual_scheme=parts[0],
                    remote_addr=request.META.get('REMOTE_ADDR')
                )
            return None

        token = " ".join(parts[1:])
        
        # Basic token format validation (JWT has 3 parts separated by dots)
        if token.count('.') != 2:
            if settings.DEBUG:
                logger.warning(
                    "invalid_jwt_format",
                    description="Invalid JWT format",
                    remote_addr=request.META.get('REMOTE_ADDR')
                )
            return None
        
        return token


class JWTCookieAuthMiddleware(JWTAuthBaseMiddleware):
    """
    JWT authentication middleware that extracts token from cookies.
    Stateless authentication without database lookup.
    """
    param_name = ACCESS_TOKEN_COOKIE
    
    def get_token_from_request(self, request: HttpRequest) -> Optional[str]:
        """
        Extract JWT token from cookies with CSRF protection.
        
        CSRF check is required for cookie-based authentication to prevent
        cross-site request forgery attacks.
        
        Override to customize cookie name or CSRF behavior.
        
        Raises:
            PermissionDenied: If CSRF check fails
        """
        # CSRF protection for cookie-based auth
        error_response = check_csrf(request)
        if error_response:
            logger.warning(
                "csrf_check_failed",
                description="CSRF validation failed for cookie-based JWT auth",
                path=request.path,
                remote_addr=request.META.get('REMOTE_ADDR'),
                cookie_name=self.param_name
            )
            raise PermissionDenied("CSRF check failed")
        
        return request.COOKIES.get(self.param_name, None)


class BasicNoPasswordAuthMiddleware:
    """
    DEVELOPMENT ONLY: Basic authentication middleware without password verification.
    
    WARNING: This middleware bypasses password authentication and should ONLY be used
    in development environments. It allows authentication by providing only a username/email
    in the Authorization header using Basic auth format.
    
    This middleware automatically disables itself when settings.DEBUG is False.
    
    Usage:
        Authorization: Basic base64(username:)
        or
        Authorization: Basic base64(username:anything)
    
    Example:
        # For user "admin@example.com"
        # Base64 encode: "admin@example.com:"
        # Header: Authorization: Basic YWRtaW5AZXhhbXBsZS5jb206
    
    IMPORTANT: Remove this middleware before deploying to production!
    """
    
    header = "Authorization"
    scheme = "basic"
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.user_model = get_user_model()
        
        # Check if in debug mode - disable completely if not
        self._enabled = settings.DEBUG
        
        if self._enabled:
            # Warning log on initialization
            logger.warning(
                "insecure_middleware_loaded",
                description="BasicNoPasswordAuthMiddleware loaded - THIS IS INSECURE AND FOR DEVELOPMENT ONLY",
                middleware=self.__class__.__name__
            )
        else:
            # Log that middleware is disabled
            logger.info(
                "insecure_middleware_disabled",
                description="BasicNoPasswordAuthMiddleware disabled in non-DEBUG mode",
                middleware=self.__class__.__name__
            )
    
    def __call__(self, request: HttpRequest):
        """
        Process the request through the middleware.
        If not in DEBUG mode, simply passes through without any processing.
        """
        if not self._enabled:
            return self.get_response(request)
        
        self.process_request(request)
        return self.get_response(request)
    
    def process_request(self, request: HttpRequest):
        """
        Process request and authenticate user if Basic auth header is present.
        Skips if user is already authenticated.
        Note: This method is only called when DEBUG is True.
        """
        # Skip if already authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            return
        
        auth_header = request.headers.get(self.header)
        if not auth_header:
            return
        
        try:
            user = self._authenticate(auth_header)
            if user:
                request.user = user
                logger.info(
                    "dev_auth_success",
                    description="Development authentication successful",
                    user_id=user.id,
                    username=user.email,
                    path=request.path
                )
        except Exception as e:
            logger.debug(
                "dev_auth_failed",
                description="Development authentication failed",
                error=str(e),
                path=request.path
            )
    
    def _authenticate(self, auth_header: str) -> Optional[AbstractBaseUser]:
        """
        Extract credentials from Basic auth header and authenticate user without password.
        
        Args:
            auth_header: The Authorization header value
            
        Returns:
            User object if found and active, None otherwise
        """
        parts = auth_header.split(" ")
        
        # Validate scheme
        if len(parts) != 2 or parts[0].lower() != self.scheme:
            return None
        
        # Decode base64 credentials
        import base64
        try:
            encoded_credentials = parts[1]
            decoded_bytes = base64.b64decode(encoded_credentials)
            decoded_credentials = decoded_bytes.decode('utf-8')
        except Exception:
            logger.debug("Failed to decode base64 credentials")
            return None
        
        # Split username:password (password is ignored)
        if ':' in decoded_credentials:
            username, _ = decoded_credentials.split(':', 1)
        else:
            username = decoded_credentials
        
        if not username:
            return None
        
        # Find user by email or username
        try:
            user = self.user_model.objects.get(email=username)
        except self.user_model.DoesNotExist:
            try:
                # Try by username field if different from email
                user = self.user_model.objects.get(**{self.user_model.USERNAME_FIELD: username})
            except (self.user_model.DoesNotExist, AttributeError):
                logger.debug(f"User not found: {username}")
                return None
        
        # Check if user is active
        if not user.is_active:
            logger.debug(f"User {username} is inactive")
            return None
        
        return user

