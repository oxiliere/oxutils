"""
Pytest configuration and fixtures for auth tests.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest


@pytest.fixture
def mock_request_factory():
    """Provide Django RequestFactory."""
    from django.test import RequestFactory

    return RequestFactory()


@pytest.fixture
def mock_http_request(mock_request_factory):
    """Provide a mock HTTP request with common attributes."""
    request = mock_request_factory.get("/")
    request.user = Mock()
    request.user.id = 1
    request.user.pk = 1
    request.user.email = "test@example.com"
    request.user.is_authenticated = True
    request.user.is_active = True
    request.user.check_password = Mock(return_value=True)
    request.COOKIES = {}
    request.META = {"REMOTE_ADDR": "127.0.0.1"}
    request.headers = {"Authorization": "Bearer test-token"}
    return request


@pytest.fixture
def mock_user_model():
    """Provide a mock User model."""
    with patch("django.contrib.auth.get_user_model") as mock:
        User = MagicMock()
        User.USERNAME_FIELD = "email"
        User.objects = MagicMock()
        User.DoesNotExist = Exception
        mock.return_value = User
        yield User


@pytest.fixture
def mock_email_address():
    """Provide a mock EmailAddress queryset."""
    with patch("allauth.account.models.EmailAddress.objects") as mock_qs:
        mock_qs.filter.return_value = mock_qs
        mock_qs.exists.return_value = False
        mock_qs.delete.return_value = None
        mock_qs.get_for_user.return_value = None
        yield mock_qs


@pytest.fixture
def mock_allauth_adapter():
    """Provide a mock allauth adapter."""
    with patch("allauth.account.adapter.get_adapter") as mock:
        adapter = MagicMock()
        adapter.clean_email = lambda email: email.strip().lower()
        adapter.authenticate.return_value = None
        mock.return_value = adapter
        yield adapter


@pytest.fixture
def mock_allauth_context():
    """Mock allauth request context."""
    with patch("oxutils.auth.adapter.allauth_ctx") as mock:
        mock.request = None
        yield mock


@pytest.fixture
def mock_render_to_string():
    """Mock Django template rendering."""
    with patch("oxutils.auth.adapter.render_to_string") as mock:
        mock.return_value = "Rendered template content"
        yield mock


@pytest.fixture
def mock_get_current_site():
    """Mock get_current_site."""
    with patch("oxutils.auth.adapter.get_current_site") as mock:
        site = Mock()
        site.domain = "example.com"
        site.name = "Example"
        mock.return_value = site
        yield mock


@pytest.fixture
def mock_settings():
    """Provide mocked Django settings with auth defaults."""
    with patch("oxutils.auth.utils.settings") as mock:
        mock.DEBUG = True
        mock.JWT_ALLAUTH_COLLECT_USER_AGENT = False
        mock.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        mock.JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE = True
        mock.OXI_COOKIE_DOMAIN = "example.com"
        mock.TEMPLATE_PATHS = {}
        mock.OLD_PASSWORD_FIELD_ENABLED = True
        mock.LOGOUT_ON_PASSWORD_CHANGE = True
        mock.ACCOUNT_FRONTEND_URLS = {
            "account_confirm_email": "https://app.example.com/confirm-email/{key}",
            "account_reset_password": "https://app.example.com/reset-password/{uid}/{token}",
        }
        yield mock


@pytest.fixture
def mock_allauth_app_settings():
    """Mock allauth account app_settings."""
    with patch("oxutils.auth.adapter.allauth_app_settings") as mock:
        mock.UNIQUE_EMAIL = True
        mock.EMAIL_VERIFICATION_BY_CODE_ENABLED = False
        mock.TEMPLATE_EXTENSION = "html"
        yield mock


@pytest.fixture
def mock_user_agent_django():
    """Mock django-user-agents get_user_agent."""
    with patch("oxutils.auth.utils.get_user_agent_django") as mock:
        ua = Mock()
        ua.browser.family = "Chrome"
        ua.browser.version_string = "120.0"
        ua.os.family = "Linux"
        ua.os.version_string = "5.15"
        ua.device.family = "Other"
        ua.device.brand = None
        ua.device.model = None
        ua.is_mobile = False
        ua.is_tablet = False
        ua.is_pc = True
        ua.is_bot = False
        mock.return_value = ua
        yield mock
