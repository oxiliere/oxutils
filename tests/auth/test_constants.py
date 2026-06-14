"""
Tests for oxutils.auth.constants module.
"""
import pytest

from oxutils.auth.constants import (
    PASS_RESET,
    PASS_RESET_ACCESS,
    TEMPLATE_PATHS,
    EMAIL_VERIFIED_REDIRECT,
    PASSWORD_RESET_REDIRECT,
    PASS_RESET_COOKIE,
    FOR_USER,
    ONE_TIME_PERMISSION,
    REFRESH_TOKEN_COOKIE,
    ACCESS_TOKEN_COOKIE,
)


class TestConstants:
    """Test auth constants values."""

    def test_pass_reset_constant(self):
        assert PASS_RESET == "PASS_RESET"

    def test_pass_reset_access_constant(self):
        assert PASS_RESET_ACCESS == "PASS_RESET_ACCESS"

    def test_template_paths_constant(self):
        assert TEMPLATE_PATHS == "JWT_ALLAUTH_TEMPLATES"

    def test_email_verified_redirect_constant(self):
        assert EMAIL_VERIFIED_REDIRECT == "EMAIL_VERIFIED_REDIRECT"

    def test_password_reset_redirect_constant(self):
        assert PASSWORD_RESET_REDIRECT == "PASSWORD_RESET_REDIRECT"

    def test_pass_reset_cookie_constant(self):
        assert PASS_RESET_COOKIE == "password_reset_access_token"

    def test_for_user_constant(self):
        assert FOR_USER == "for_user"

    def test_one_time_permission_constant(self):
        assert ONE_TIME_PERMISSION == "one_time_permission"

    def test_refresh_token_cookie_constant(self):
        assert REFRESH_TOKEN_COOKIE == "refresh_token"

    def test_access_token_cookie_constant(self):
        assert ACCESS_TOKEN_COOKIE == "access_token"

    def test_all_constants_are_strings(self):
        constants = [
            PASS_RESET,
            PASS_RESET_ACCESS,
            TEMPLATE_PATHS,
            EMAIL_VERIFIED_REDIRECT,
            PASSWORD_RESET_REDIRECT,
            PASS_RESET_COOKIE,
            FOR_USER,
            ONE_TIME_PERMISSION,
            REFRESH_TOKEN_COOKIE,
            ACCESS_TOKEN_COOKIE,
        ]
        for const in constants:
            assert isinstance(const, str)
