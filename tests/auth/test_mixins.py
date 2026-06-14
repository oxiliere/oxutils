"""
Tests for oxutils.auth.mixins module.
"""

from unittest.mock import Mock, patch


def _configure_mock_settings(mock_settings, **overrides):
    """Apply settings overrides, then force-set secure defaults for absent keys."""
    # Apply user overrides first
    for k, v in overrides.items():
        setattr(mock_settings, k, v)

    # Define defaults as a dict and only set on the mock if not already provided
    defaults = {
        "AUTH_COOKIE_HTTP_ONLY": True,
        "AUTH_COOKIE_SAME_SITE": "Lax",
        "OXI_COOKIE_DOMAIN": "example.com",
        "JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE": True,
    }
    for key, default_value in defaults.items():
        if key not in overrides:
            setattr(mock_settings, key, default_value)

    # Derive AUTH_COOKIE_SECURE from DEBUG unless explicitly set
    if "AUTH_COOKIE_SECURE" not in overrides:
        debug = overrides.get("DEBUG", getattr(mock_settings, "DEBUG", True))
        setattr(mock_settings, "AUTH_COOKIE_SECURE", not debug)


class TestCookieTokenMixin:
    """Tests for CookieTokenMixin."""

    @patch("oxutils.auth.mixins.settings")
    def test_set_token_cookie_with_refresh(self, mock_settings):
        from oxutils.auth.mixins import CookieTokenMixin

        _configure_mock_settings(mock_settings, DEBUG=True)

        mixin = CookieTokenMixin()
        response = Mock()
        mixin.context = Mock()
        mixin.context.response = response

        mixin.set_token_cookie(access_token="access123", refresh_token="refresh456")

        response.set_cookie.assert_any_call(
            key="access_token",
            value="access123",
            httponly=True,
            domain="example.com",
            secure=False,
            samesite="Lax",
        )
        response.set_cookie.assert_any_call(
            key="refresh_token",
            value="refresh456",
            httponly=True,
            domain="example.com",
            secure=False,
            samesite="Lax",
        )

    @patch("oxutils.auth.mixins.settings")
    def test_set_token_cookie_without_refresh(self, mock_settings):
        from oxutils.auth.mixins import CookieTokenMixin

        _configure_mock_settings(
            mock_settings, DEBUG=True, JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE=False
        )

        mixin = CookieTokenMixin()
        response = Mock()
        mixin.context = Mock()
        mixin.context.response = response

        mixin.set_token_cookie(access_token="access123", refresh_token="refresh456")

        response.set_cookie.assert_called_once_with(
            key="access_token",
            value="access123",
            httponly=True,
            domain="example.com",
            secure=False,
            samesite="Lax",
        )

    @patch("oxutils.auth.mixins.settings")
    def test_set_token_cookie_secure_in_production(self, mock_settings):
        from oxutils.auth.mixins import CookieTokenMixin

        _configure_mock_settings(mock_settings, DEBUG=False)

        mixin = CookieTokenMixin()
        response = Mock()
        mixin.context = Mock()
        mixin.context.response = response

        mixin.set_token_cookie(access_token="access123", refresh_token="refresh456")

        response.set_cookie.assert_any_call(
            key="access_token",
            value="access123",
            httponly=True,
            domain="example.com",
            secure=True,
            samesite="Lax",
        )

    @patch("oxutils.auth.mixins.settings")
    def test_remove_token_cookie_with_refresh_enabled(self, mock_settings):
        from oxutils.auth.mixins import CookieTokenMixin

        _configure_mock_settings(mock_settings)

        mixin = CookieTokenMixin()
        response = Mock()
        mixin.context = Mock()
        mixin.context.response = response

        mixin.remove_token_cookie()

        response.delete_cookie.assert_any_call(
            key="refresh_token", domain="example.com", samesite="Lax"
        )
        response.delete_cookie.assert_any_call(
            key="access_token", domain="example.com", samesite="Lax"
        )

    @patch("oxutils.auth.mixins.settings")
    def test_remove_token_cookie_without_refresh(self, mock_settings):
        from oxutils.auth.mixins import CookieTokenMixin

        _configure_mock_settings(mock_settings, JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE=False)

        mixin = CookieTokenMixin()
        response = Mock()
        mixin.context = Mock()
        mixin.context.response = response

        mixin.remove_token_cookie()

        response.delete_cookie.assert_called_once_with(
            key="access_token", domain="example.com", samesite="Lax"
        )

    @patch("oxutils.auth.mixins.settings")
    def test_set_token_cookie_without_debug_attribute(self, mock_settings):
        from oxutils.auth.mixins import CookieTokenMixin

        _configure_mock_settings(mock_settings)
        # Delete DEBUG but keep the derived AUTH_COOKIE_SECURE=True as default
        del mock_settings.DEBUG
        mock_settings.AUTH_COOKIE_SECURE = True

        mixin = CookieTokenMixin()
        response = Mock()
        mixin.context = Mock()
        mixin.context.response = response

        mixin.set_token_cookie(access_token="access123", refresh_token="refresh456")

        response.set_cookie.assert_any_call(
            key="access_token",
            value="access123",
            httponly=True,
            domain="example.com",
            secure=True,
            samesite="Lax",
        )

    @patch("oxutils.auth.mixins.settings")
    def test_custom_cookie_settings(self, mock_settings):
        """Test that custom AUTH_COOKIE_* settings are respected."""
        from oxutils.auth.mixins import CookieTokenMixin

        _configure_mock_settings(
            mock_settings,
            DEBUG=False,
            AUTH_COOKIE_HTTP_ONLY=False,
            AUTH_COOKIE_SECURE=True,
            AUTH_COOKIE_SAME_SITE="Strict",
        )

        mixin = CookieTokenMixin()
        response = Mock()
        mixin.context = Mock()
        mixin.context.response = response

        mixin.set_token_cookie(access_token="access123", refresh_token="refresh456")

        response.set_cookie.assert_any_call(
            key="access_token",
            value="access123",
            httponly=False,
            domain="example.com",
            secure=True,
            samesite="Strict",
        )
