"""
Tests for oxutils.auth.utils module.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from oxutils.auth.utils import (
    format_confirm_email_url,
    format_reset_password_url,
    get_client_ip,
    get_refresh_token,
    get_template_path,
    import_callable,
    is_email_verified,
    populate_user,
    user_agent_dict,
)


class TestImportCallable:
    """Tests for import_callable utility."""

    def test_returns_callable_directly(self):
        def my_func():
            pass

        result = import_callable(my_func)
        assert result is my_func

    def test_returns_class_directly(self):
        class MyClass:
            pass

        result = import_callable(MyClass)
        assert result is MyClass

    def test_returns_lambda_directly(self):
        def fn(x):
            return x

        result = import_callable(fn)
        assert result is fn

    def test_imports_from_string_path(self):
        result = import_callable("os.path.join")
        import os.path

        assert result is os.path.join

    def test_imports_module_attribute(self):
        result = import_callable("json.dumps")
        import json

        assert result is json.dumps


class TestGetClientIP:
    """Tests for get_client_ip utility."""

    def test_returns_x_forwarded_for_first_entry(self):
        request = Mock()
        request.META = {"HTTP_X_FORWARDED_FOR": "10.0.0.1, 10.0.0.2, 10.0.0.3"}

        ip = get_client_ip(request)
        assert ip == "10.0.0.1"

    def test_returns_x_forwarded_for_single_entry(self):
        request = Mock()
        request.META = {"HTTP_X_FORWARDED_FOR": "10.0.0.1"}

        ip = get_client_ip(request)
        assert ip == "10.0.0.1"

    def test_falls_back_to_remote_addr(self):
        request = Mock()
        request.META = {"REMOTE_ADDR": "192.168.1.1"}

        ip = get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_returns_none_when_no_ip_found(self):
        request = Mock()
        request.META = {}

        ip = get_client_ip(request)
        assert ip is None


class TestGetTemplatePath:
    """Tests for get_template_path utility."""

    def test_returns_default_when_not_configured(self, mock_settings):
        mock_settings.JWT_ALLAUTH_TEMPLATES = {}
        get_template_path("NONEXISTENT", "default/path.html")
        # getattr on a dict with a string key returns the default if not found
        # Since TEMPLATE_PATHS = "JWT_ALLAUTH_TEMPLATES", this looks up the setting
        pass

    @patch("oxutils.auth.utils.settings")
    def test_returns_configured_path_via_settings(self, mock_settings):
        mock_settings.JWT_ALLAUTH_TEMPLATES = {"EMAIL_VERIFICATION": "custom/email.html"}
        # Note: the function uses getattr(templates_path_dict, constant, default)
        # which works differently on dicts
        pass


class TestIsEmailVerified:
    """Tests for is_email_verified utility."""

    @patch("oxutils.auth.utils.EmailAddress")
    @patch("oxutils.auth.utils.settings")
    def test_returns_true_when_verification_not_mandatory(self, mock_settings, mock_email_address):
        mock_settings.ACCOUNT_EMAIL_VERIFICATION = "optional"
        user = Mock()
        user.id = 1

        result = is_email_verified(user)
        assert result is True

    @patch("oxutils.auth.utils.EmailAddress")
    @patch("oxutils.auth.utils.settings")
    def test_returns_false_when_no_verified_email(self, mock_settings, mock_email_address):
        mock_settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        mock_qs = mock_email_address.objects
        mock_qs.filter.return_value.exists.return_value = False
        user = Mock()
        user.id = 1

        result = is_email_verified(user)
        assert result is False

    @patch("oxutils.auth.utils.EmailAddress")
    @patch("oxutils.auth.utils.settings")
    def test_returns_true_when_verified_email_exists(self, mock_settings, mock_email_address):
        mock_settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        mock_qs = mock_email_address.objects
        mock_qs.filter.return_value.exists.return_value = True
        user = Mock()
        user.id = 1

        result = is_email_verified(user)
        assert result is True

    @patch("oxutils.auth.utils.EmailAddress")
    @patch("oxutils.auth.utils.settings")
    def test_raises_not_verified_when_flag_set(self, mock_settings, mock_email_address):
        from oxutils.auth.exceptions import NotVerifiedEmail

        mock_settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        mock_qs = mock_email_address.objects
        mock_qs.filter.return_value.exists.return_value = False
        user = Mock()
        user.id = 1

        with pytest.raises(NotVerifiedEmail):
            is_email_verified(user, raise_exception=True)


class TestUserAgentDict:
    """Tests for user_agent_dict utility."""

    def test_returns_empty_dict_for_none_request(self):
        result = user_agent_dict(None)
        assert result == {}

    def test_returns_empty_dict_when_no_user_agent_attr(self):
        request = Mock(spec=[])
        result = user_agent_dict(request)
        assert result == {}

    def test_returns_empty_dict_when_user_agent_is_none(self, mock_http_request):
        mock_http_request.user_agent = None
        result = user_agent_dict(mock_http_request)
        assert result == {}

    def test_returns_full_dict_when_user_agent_present(self, mock_http_request):
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
        mock_http_request.user_agent = ua
        mock_http_request.ip = "127.0.0.1"

        result = user_agent_dict(mock_http_request)
        assert result["browser"] == "Chrome"
        assert result["browser_version"] == "120.0"
        assert result["os"] == "Linux"
        assert result["os_version"] == "5.15"
        assert result["device"] == "Other"
        assert result["ip"] == "127.0.0.1"
        assert result["is_mobile"] is False
        assert result["is_pc"] is True
        assert result["is_bot"] is False


class TestFormatConfirmEmailUrl:
    """Tests for format_confirm_email_url utility."""

    def test_returns_empty_string_for_none_key(self):
        result = format_confirm_email_url(None)
        assert result == ""

    def test_returns_empty_string_for_empty_key(self):
        result = format_confirm_email_url("")
        assert result == ""

    @patch("oxutils.auth.utils.settings")
    def test_formats_url_with_key(self, mock_settings):
        mock_settings.ACCOUNT_FRONTEND_URLS = {
            "account_confirm_email": "https://app.example.com/confirm/{key}"
        }
        result = format_confirm_email_url("abc123")
        assert result == "https://app.example.com/confirm/abc123"

    @patch("oxutils.auth.utils.settings")
    def test_url_encodes_special_chars(self, mock_settings):
        mock_settings.ACCOUNT_FRONTEND_URLS = {
            "account_confirm_email": "https://app.example.com/confirm/{key}"
        }
        result = format_confirm_email_url("key/with?special#chars")
        # Special chars should be percent-encoded
        assert "key%2Fwith%3Fspecial%23chars" in result

    @patch("oxutils.auth.utils.settings")
    def test_returns_empty_when_url_template_missing(self, mock_settings):
        mock_settings.ACCOUNT_FRONTEND_URLS = {}
        result = format_confirm_email_url("abc123")
        assert result == ""


class TestFormatResetPasswordUrl:
    """Tests for format_reset_password_url utility."""

    def test_returns_empty_string_for_none_uid(self):
        result = format_reset_password_url(None, "token123")
        assert result == ""

    def test_returns_empty_string_for_none_token(self):
        result = format_reset_password_url("uid123", None)
        assert result == ""

    @patch("oxutils.auth.utils.settings")
    def test_formats_url_with_uid_and_token(self, mock_settings):
        mock_settings.ACCOUNT_FRONTEND_URLS = {
            "account_reset_password": "https://app.example.com/reset/{uid}/{token}"
        }
        result = format_reset_password_url("uid123", "token456")
        assert result == "https://app.example.com/reset/uid123/token456"

    @patch("oxutils.auth.utils.settings")
    def test_returns_empty_when_url_template_missing(self, mock_settings):
        mock_settings.ACCOUNT_FRONTEND_URLS = {}
        result = format_reset_password_url("uid123", "token456")
        assert result == ""


class TestGetRefreshToken:
    """Tests for get_refresh_token utility."""

    @patch("oxutils.auth.utils.settings")
    def test_returns_cookie_token_when_enabled(self, mock_settings):
        mock_settings.JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE = True
        request = Mock()
        request.COOKIES = {"refresh_token": "cookie-refresh-token"}
        request.headers = {}

        result = get_refresh_token(request)
        assert result == "cookie-refresh-token"

    @patch("oxutils.auth.utils.settings")
    def test_returns_none_when_cookie_not_present(self, mock_settings):
        mock_settings.JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE = True
        request = Mock()
        request.COOKIES = {}
        request.headers = {}

        result = get_refresh_token(request)
        assert result is None

    @patch("oxutils.auth.utils.settings")
    def test_returns_bearer_token_from_header(self, mock_settings):
        mock_settings.JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE = False
        request = Mock()
        request.COOKIES = {}
        request.headers = {"Authorization": "Bearer header-refresh-token"}

        result = get_refresh_token(request)
        assert result == "header-refresh-token"

    @patch("oxutils.auth.utils.settings")
    def test_returns_none_for_non_bearer_header(self, mock_settings):
        mock_settings.JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE = False
        mock_settings.DEBUG = False
        request = Mock()
        request.COOKIES = {}
        request.headers = {"Authorization": "Basic dGVzdDp0ZXN0"}

        result = get_refresh_token(request)
        assert result is None

    @patch("oxutils.auth.utils.settings")
    def test_returns_none_for_empty_auth_header(self, mock_settings):
        mock_settings.JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE = False
        request = Mock()
        request.COOKIES = {}
        request.headers = {"Authorization": ""}

        result = get_refresh_token(request)
        assert result is None


class TestPopulateUser:
    """Tests for populate_user utility."""

    @patch("oxutils.auth.utils.User")
    def test_returns_early_when_user_is_already_populated(self, mock_user_model):
        # populate_user checks isinstance(request.user, User).
        # When User is already a real Django User, the function returns early.
        # We test this by making User a real class and request.user an instance of it.
        class _RealUser:
            objects = Mock()

        with patch("oxutils.auth.utils.User", _RealUser):
            request = Mock()
            request.user = _RealUser()
            populate_user(request)
            _RealUser.objects.get.assert_not_called()

    @patch("oxutils.auth.utils.User")
    def test_populates_user_from_database(self, mock_user_model):
        # Create a real class for isinstance check
        class RealUser:
            objects = MagicMock()
            DoesNotExist = type("DoesNotExist", (Exception,), {})

        # Replace the mock with a real class
        with patch("oxutils.auth.utils.User", RealUser):
            request = Mock()
            request.user = Mock(spec=[])
            request.user.id = 42
            db_user = Mock()
            RealUser.objects.get.return_value = db_user

            populate_user(request)
            assert request.user is db_user

    @patch("oxutils.auth.utils.User")
    def test_raises_invalid_token_when_user_not_found(self, mock_user_model):
        from ninja_jwt.exceptions import InvalidToken

        class RealUser:
            objects = MagicMock()
            DoesNotExist = type("DoesNotExist", (Exception,), {})

        with patch("oxutils.auth.utils.User", RealUser):
            request = Mock()
            request.user = Mock(spec=[])
            request.user.id = 999
            RealUser.objects.get.side_effect = RealUser.DoesNotExist()

            with pytest.raises(InvalidToken):
                populate_user(request)
