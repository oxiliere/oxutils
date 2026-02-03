"""
Tests for JWT middleware authentication.

Tests the following middlewares:
- JWTHeaderAuthMiddleware: Token extraction from Authorization header
- JWTCookieAuthMiddleware: Token extraction from cookies with CSRF protection
- BasicNoPasswordAuthMiddleware: Development-only basic auth without password
"""

import base64
import pytest
from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

from oxutils.jwt.middleware import (
    JWTAuthBaseMiddleware,
    JWTHeaderAuthMiddleware,
    JWTCookieAuthMiddleware,
    BasicNoPasswordAuthMiddleware,
)
from ninja_jwt.exceptions import InvalidToken
from ninja_jwt.tokens import AccessToken


User = get_user_model()


@pytest.fixture
def mock_get_response():
    """Mock get_response function for middleware initialization."""
    return Mock(return_value=Mock(status_code=200))


@pytest.fixture
def create_request():
    """Factory to create HTTP requests with various configurations."""
    def _create_request(
        method="GET",
        auth_header=None,
        cookies=None,
        remote_addr="127.0.0.1",
        user=None,
    ):
        request = HttpRequest()
        request.method = method
        request.META = {
            "REMOTE_ADDR": remote_addr,
            "HTTP_USER_AGENT": "TestAgent",
        }
        
        if auth_header:
            request.META["HTTP_AUTHORIZATION"] = auth_header
        
        if cookies:
            request.COOKIES = cookies
        else:
            request.COOKIES = {}
        
        # Initialize with AnonymousUser by default
        request.user = user if user else AnonymousUser()
        
        return request
    
    return _create_request


@pytest.fixture
def active_user(db):
    """Create an active user for testing."""
    return User.objects.create_user(
        username="active_user",
        email="test@example.com",
        password="testpass123",
        is_active=True,
    )


@pytest.fixture
def inactive_user(db):
    """Create an inactive user for testing."""
    return User.objects.create_user(
        username="inactive_user",
        email="inactive@example.com",
        password="testpass123",
        is_active=False,
    )


class TestJWTAuthBaseMiddleware:
    """Tests for the base JWT authentication middleware."""
    
    def test_middleware_initialization(self, mock_get_response):
        """Test middleware initializes correctly."""
        middleware = JWTAuthBaseMiddleware(mock_get_response)
        
        assert middleware.get_response == mock_get_response
        assert middleware.user_model == User
    
    def test_get_token_from_request_not_implemented(self, mock_get_response, create_request):
        """Test that base middleware requires subclass implementation."""
        middleware = JWTAuthBaseMiddleware(mock_get_response)
        request = create_request()
        
        with pytest.raises(NotImplementedError, match="Subclasses must implement"):
            middleware.get_token_from_request(request)
    
    def test_process_request_skips_if_already_authenticated(
        self, mock_get_response, create_request, active_user
    ):
        """Test that middleware skips if user is already authenticated."""
        middleware = JWTAuthBaseMiddleware(mock_get_response)
        request = create_request(user=active_user)
        
        # Should not raise NotImplementedError because it skips early
        middleware.process_request(request)
        
        assert request.user == active_user
    
    def test_process_request_anonymous_user(self, mock_get_response, create_request):
        """Test that middleware attempts auth for anonymous users."""
        middleware = JWTAuthBaseMiddleware(mock_get_response)
        request = create_request()
        
        # Will fail because get_token_from_request is not implemented
        with pytest.raises(NotImplementedError):
            middleware.process_request(request)


class TestJWTHeaderAuthMiddleware:
    """Tests for JWT header authentication middleware."""
    
    def test_extract_valid_token(self, mock_get_response, create_request):
        """Test extracting a valid JWT token from header."""
        middleware = JWTHeaderAuthMiddleware(mock_get_response)
        token = "valid.jwt.token"
        request = create_request(auth_header=f"Bearer {token}")
        
        extracted = middleware.get_token_from_request(request)
        
        assert extracted == token
    
    def test_extract_token_without_bearer_prefix(self, mock_get_response, create_request):
        """Test that token without Bearer prefix is rejected."""
        middleware = JWTHeaderAuthMiddleware(mock_get_response)
        request = create_request(auth_header="valid.jwt.token")
        
        extracted = middleware.get_token_from_request(request)
        
        assert extracted is None
    
    def test_extract_token_wrong_scheme(self, mock_get_response, create_request):
        """Test that wrong scheme (Basic instead of Bearer) is rejected."""
        middleware = JWTHeaderAuthMiddleware(mock_get_response)
        request = create_request(auth_header="Basic dXNlcjpwYXNz")
        
        extracted = middleware.get_token_from_request(request)
        
        assert extracted is None
    
    def test_extract_token_missing_header(self, mock_get_response, create_request):
        """Test that missing Authorization header returns None."""
        middleware = JWTHeaderAuthMiddleware(mock_get_response)
        request = create_request()
        
        extracted = middleware.get_token_from_request(request)
        
        assert extracted is None
    
    def test_extract_token_invalid_format(self, mock_get_response, create_request):
        """Test that invalid JWT format (not 3 parts) is rejected."""
        middleware = JWTHeaderAuthMiddleware(mock_get_response)
        request = create_request(auth_header="Bearer invalid.token")
        
        extracted = middleware.get_token_from_request(request)
        
        assert extracted is None
    
    def test_extract_token_case_insensitive_bearer(self, mock_get_response, create_request):
        """Test that bearer scheme is case-insensitive."""
        middleware = JWTHeaderAuthMiddleware(mock_get_response)
        token = "valid.jwt.token"
        request = create_request(auth_header=f"bearer {token}")
        
        extracted = middleware.get_token_from_request(request)
        
        assert extracted == token
    
    def test_process_request_valid_token(
        self, mock_get_response, create_request, active_user, settings
    ):
        """Test full authentication flow with valid token."""
        settings.DEBUG = True
        
        middleware = JWTHeaderAuthMiddleware(mock_get_response)
        token = str(AccessToken.for_user(active_user))
        request = create_request(auth_header=f"Bearer {token}")
        
        middleware.process_request(request)
        
        assert request.user.is_authenticated
        assert request.user.id == active_user.id
        assert hasattr(request, 'token_user')
    
    def test_process_request_invalid_token(self, mock_get_response, create_request, settings):
        """Test that invalid token results in anonymous user."""
        settings.DEBUG = True
        
        middleware = JWTHeaderAuthMiddleware(mock_get_response)
        request = create_request(auth_header="Bearer invalid.jwt.token")
        
        middleware.process_request(request)
        
        assert not request.user.is_authenticated
        assert isinstance(request.user, AnonymousUser)


class TestJWTCookieAuthMiddleware:
    """Tests for JWT cookie authentication middleware."""
    
    def test_extract_valid_token_from_cookie(self, mock_get_response, create_request):
        """Test extracting token from cookie."""
        middleware = JWTCookieAuthMiddleware(mock_get_response)
        token = "valid.jwt.token"
        request = create_request(cookies={"access_token": token})
        
        with patch("oxutils.jwt.middleware.check_csrf", return_value=None):
            extracted = middleware.get_token_from_request(request)
        
        assert extracted == token
    
    def test_extract_missing_cookie(self, mock_get_response, create_request):
        """Test that missing cookie returns None."""
        middleware = JWTCookieAuthMiddleware(mock_get_response)
        request = create_request()
        
        with patch("oxutils.jwt.middleware.check_csrf", return_value=None):
            extracted = middleware.get_token_from_request(request)
        
        assert extracted is None
    
    def test_csrf_check_fails(self, mock_get_response, create_request):
        """Test that CSRF failure raises PermissionDenied."""
        middleware = JWTCookieAuthMiddleware(mock_get_response)
        request = create_request(cookies={"access_token": "valid.token"})
        
        with patch("oxutils.jwt.middleware.check_csrf", return_value=Mock()):
            with pytest.raises(PermissionDenied, match="CSRF check failed"):
                middleware.get_token_from_request(request)
    
    def test_process_request_handles_csrf_failure(
        self, mock_get_response, create_request, settings
    ):
        """Test that CSRF failure in process_request sets anonymous user."""
        settings.DEBUG = True
        
        middleware = JWTCookieAuthMiddleware(mock_get_response)
        request = create_request(cookies={"access_token": "valid.token"})
        
        with patch("oxutils.jwt.middleware.check_csrf", return_value=Mock()):
            middleware.process_request(request)
        
        assert not request.user.is_authenticated
        assert isinstance(request.user, AnonymousUser)
    
    def test_custom_cookie_name(self, mock_get_response, create_request):
        """Test that custom cookie name can be used."""
        class CustomCookieMiddleware(JWTCookieAuthMiddleware):
            param_name = "custom_token"
        
        middleware = CustomCookieMiddleware(mock_get_response)
        token = "valid.jwt.token"
        request = create_request(cookies={"custom_token": token})
        
        with patch("oxutils.jwt.middleware.check_csrf", return_value=None):
            extracted = middleware.get_token_from_request(request)
        
        assert extracted == token


class TestBasicNoPasswordAuthMiddleware:
    """Tests for development-only basic auth middleware."""
    
    def test_middleware_disabled_in_production(self, mock_get_response, settings):
        """Test that middleware is disabled when DEBUG is False."""
        settings.DEBUG = False
        
        middleware = BasicNoPasswordAuthMiddleware(mock_get_response)
        
        assert not middleware._enabled
    
    def test_middleware_enabled_in_debug(self, mock_get_response, settings):
        """Test that middleware is enabled when DEBUG is True."""
        settings.DEBUG = True
        
        middleware = BasicNoPasswordAuthMiddleware(mock_get_response)
        
        assert middleware._enabled
    
    def test_bypass_in_production_mode(self, mock_get_response, create_request, settings):
        """Test that middleware bypasses completely in production."""
        settings.DEBUG = False
        
        middleware = BasicNoPasswordAuthMiddleware(mock_get_response)
        request = create_request()
        
        # Should not process the request at all
        response = middleware(request)
        
        assert middleware.get_response.called
        assert not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated
    
    def test_valid_basic_auth_header(self, mock_get_response, create_request, active_user, settings):
        """Test authentication with valid Basic auth header."""
        settings.DEBUG = True
        
        middleware = BasicNoPasswordAuthMiddleware(mock_get_response)
        credentials = base64.b64encode(f"{active_user.email}:anything".encode()).decode()
        request = create_request(auth_header=f"Basic {credentials}")
        
        middleware.process_request(request)
        
        assert request.user.is_authenticated
        assert request.user.id == active_user.id
    
    def test_basic_auth_without_password(self, mock_get_response, create_request, active_user, settings):
        """Test authentication with username only (no password)."""
        settings.DEBUG = True
        
        middleware = BasicNoPasswordAuthMiddleware(mock_get_response)
        credentials = base64.b64encode(f"{active_user.email}:".encode()).decode()
        request = create_request(auth_header=f"Basic {credentials}")
        
        middleware.process_request(request)
        
        assert request.user.is_authenticated
        assert request.user.id == active_user.id
    
    def test_basic_auth_inactive_user(self, mock_get_response, create_request, inactive_user, settings):
        """Test that inactive users cannot authenticate."""
        settings.DEBUG = True
        
        middleware = BasicNoPasswordAuthMiddleware(mock_get_response)
        credentials = base64.b64encode(f"{inactive_user.email}:anything".encode()).decode()
        request = create_request(auth_header=f"Basic {inactive_user.email}")
        
        middleware.process_request(request)
        
        assert not request.user.is_authenticated
    
    def test_basic_auth_nonexistent_user(self, mock_get_response, create_request, settings):
        """Test that non-existent users cannot authenticate."""
        settings.DEBUG = True
        
        middleware = BasicNoPasswordAuthMiddleware(mock_get_response)
        credentials = base64.b64encode(b"nonexistent@example.com:anything").decode()
        request = create_request(auth_header=f"Basic {credentials}")
        
        middleware.process_request(request)
        
        assert not request.user.is_authenticated
    
    def test_basic_auth_missing_header(self, mock_get_response, create_request, settings):
        """Test that missing header results in anonymous user."""
        settings.DEBUG = True
        
        middleware = BasicNoPasswordAuthMiddleware(mock_get_response)
        request = create_request()
        
        middleware.process_request(request)
        
        assert not request.user.is_authenticated
    
    def test_basic_auth_wrong_scheme(self, mock_get_response, create_request, active_user, settings):
        """Test that wrong scheme (Bearer instead of Basic) is rejected."""
        settings.DEBUG = True
        
        middleware = BasicNoPasswordAuthMiddleware(mock_get_response)
        request = create_request(auth_header=f"Bearer {active_user.email}")
        
        middleware.process_request(request)
        
        assert not request.user.is_authenticated
    
    def test_basic_auth_invalid_base64(self, mock_get_response, create_request, settings):
        """Test that invalid base64 is handled gracefully."""
        settings.DEBUG = True
        
        middleware = BasicNoPasswordAuthMiddleware(mock_get_response)
        request = create_request(auth_header="Basic invalid!!!base64")
        
        middleware.process_request(request)
        
        assert not request.user.is_authenticated
    
    def test_skips_if_already_authenticated(
        self, mock_get_response, create_request, active_user, settings
    ):
        """Test that middleware skips if user is already authenticated."""
        settings.DEBUG = True
        
        middleware = BasicNoPasswordAuthMiddleware(mock_get_response)
        request = create_request(user=active_user)
        
        middleware.process_request(request)
        
        # Should not have changed the user
        assert request.user == active_user


class TestMiddlewareChaining:
    """Tests for chaining multiple JWT middlewares together."""
    
    def test_header_middleware_authenticates_first(
        self, mock_get_response, create_request, active_user, settings
    ):
        """Test that first successful middleware auth prevents second attempt."""
        settings.DEBUG = True
        
        token = str(AccessToken.for_user(active_user))
        request = create_request(
            auth_header=f"Bearer {token}",
            cookies={"access_token": "different.token"}
        )
        
        # First middleware (header) authenticates
        header_middleware = JWTHeaderAuthMiddleware(mock_get_response)
        header_middleware.process_request(request)
        
        assert request.user.is_authenticated
        assert request.user.id == active_user.id
        
        # Second middleware (cookie) should skip
        original_user = request.user
        with patch("oxutils.jwt.middleware.check_csrf", return_value=None):
            cookie_middleware = JWTCookieAuthMiddleware(mock_get_response)
            cookie_middleware.process_request(request)
        
        # User should not have changed
        assert request.user == original_user
    
    def test_cookie_fallback_when_header_fails(
        self, mock_get_response, create_request, active_user, settings
    ):
        """Test that cookie middleware can authenticate when header fails."""
        settings.DEBUG = True
        
        token = str(AccessToken.for_user(active_user))
        request = create_request(
            auth_header="Bearer invalid.token",
            cookies={"access_token": token}
        )
        
        # First middleware (header) fails
        header_middleware = JWTHeaderAuthMiddleware(mock_get_response)
        header_middleware.process_request(request)
        
        # User should be anonymous after header failure
        assert not request.user.is_authenticated
        
        # Second middleware (cookie) should authenticate
        with patch("oxutils.jwt.middleware.check_csrf", return_value=None):
            cookie_middleware = JWTCookieAuthMiddleware(mock_get_response)
            cookie_middleware.process_request(request)
        
        # Now user should be authenticated
        assert request.user.is_authenticated
        assert request.user.id == active_user.id


class TestJWTTokenValidation:
    """Tests for JWT token validation."""
    
    def test_get_validated_token_success(self, active_user):
        """Test successful token validation."""
        token = AccessToken.for_user(active_user)
        raw_token = str(token)
        
        validated = JWTAuthBaseMiddleware.get_validated_token(raw_token)
        
        assert validated is not None
        from ninja_jwt.settings import api_settings
        assert validated[api_settings.USER_ID_CLAIM] == active_user.id
    
    def test_get_validated_token_invalid(self):
        """Test that invalid token raises exception."""
        with pytest.raises(InvalidToken):
            JWTAuthBaseMiddleware.get_validated_token("invalid.token")
    
    def test_get_user_with_valid_token(self, mock_get_response, active_user):
        """Test extracting user from valid token."""
        middleware = JWTAuthBaseMiddleware(mock_get_response)
        token = AccessToken.for_user(active_user)
        
        user = middleware.get_user(token)
        
        assert user is not None
        assert user.id == active_user.id
    
    def test_get_user_missing_user_id_claim(self, mock_get_response):
        """Test that missing user_id claim raises InvalidToken."""
        middleware = JWTAuthBaseMiddleware(mock_get_response)
        token = AccessToken()
        
        with pytest.raises(InvalidToken, match="no recognizable user identification"):
            middleware.get_user(token)
    
    def test_get_user_invalid_user_id_type(self, mock_get_response):
        """Test that invalid user_id type raises InvalidToken."""
        middleware = JWTAuthBaseMiddleware(mock_get_response)
        token = AccessToken()
        from ninja_jwt.settings import api_settings
        token[api_settings.USER_ID_CLAIM] = None  # Invalid type
        
        with pytest.raises(InvalidToken, match="Invalid user identification format"):
            middleware.get_user(token)
    
    def test_get_user_user_id_too_long(self, mock_get_response):
        """Test that too long user_id raises InvalidToken."""
        middleware = JWTAuthBaseMiddleware(mock_get_response)
        token = AccessToken()
        from ninja_jwt.settings import api_settings
        token[api_settings.USER_ID_CLAIM] = "x" * 256  # Too long
        
        with pytest.raises(InvalidToken, match="User identification too long"):
            middleware.get_user(token)
