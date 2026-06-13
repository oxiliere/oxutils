"""
Tests for oxutils.auth.exceptions module.
"""
import pytest

from oxutils.auth.exceptions import (
    NotVerifiedEmail,
    IncorrectCredentials,
    ForbidNewSession,
    ReauthenticationRequired,
)


class TestNotVerifiedEmail:
    """Tests for NotVerifiedEmail exception."""

    def test_status_code(self):
        exc = NotVerifiedEmail()
        assert exc.status_code == 401

    def test_default_detail(self):
        exc = NotVerifiedEmail()
        detail = exc.args[0] if exc.args else exc.default_detail
        assert "email" in str(detail).lower()

    def test_default_code(self):
        assert NotVerifiedEmail.default_code == "email_not_verified"

    def test_custom_detail(self):
        exc = NotVerifiedEmail()
        assert exc.default_detail is not None


class TestIncorrectCredentials:
    """Tests for IncorrectCredentials exception."""

    def test_status_code(self):
        exc = IncorrectCredentials()
        assert exc.status_code == 401

    def test_default_detail(self):
        assert "Incorrect credentials" in IncorrectCredentials.default_detail

    def test_default_code(self):
        assert IncorrectCredentials.default_code == "incorrect_credentials"


class TestForbidNewSession:
    """Tests for ForbidNewSession exception."""

    def test_status_code(self):
        exc = ForbidNewSession()
        assert exc.status_code == 406

    def test_default_code(self):
        assert ForbidNewSession.default_code == "forbid_new_session"

    def test_has_detail_dict_mixin(self):
        """Should inherit DetailDictMixin behavior."""
        from oxutils.mixins.base import DetailDictMixin

        assert issubclass(ForbidNewSession, DetailDictMixin)

    def test_custom_detail(self):
        exc = ForbidNewSession(detail="Custom forbidden")
        assert "Custom forbidden" in str(exc)


class TestReauthenticationRequired:
    """Tests for ReauthenticationRequired exception."""

    def test_status_code(self):
        exc = ReauthenticationRequired()
        assert exc.status_code == 406

    def test_default_code(self):
        assert ReauthenticationRequired.default_code == "reauthentication_required"

    def test_has_detail_dict_mixin(self):
        from oxutils.mixins.base import DetailDictMixin

        assert issubclass(ReauthenticationRequired, DetailDictMixin)

    def test_custom_code(self):
        exc = ReauthenticationRequired(code="custom_reauth")
        assert "custom_reauth" in str(exc)
