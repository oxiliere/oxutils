"""
Tests for oxutils.auth.sessions module.
"""

from unittest.mock import Mock

import pytest


class TestUserSessionSchema:
    """Tests for UserSession schema."""

    def test_is_model_schema(self):
        from ninja import ModelSchema

        from oxutils.auth.sessions.schemas import UserSession
        from oxutils.auth.tokens.models import RefreshTokenWhitelistModel

        assert issubclass(UserSession, ModelSchema)
        assert UserSession.Meta.model is RefreshTokenWhitelistModel

    def test_excludes_jti_and_user(self):
        from oxutils.auth.sessions.schemas import UserSession

        assert "jti" in UserSession.Meta.exclude
        assert "user" in UserSession.Meta.exclude

    def test_has_is_current_field(self):
        from oxutils.auth.sessions.schemas import UserSession

        assert "is_current" in UserSession.model_fields


class TestUserSessionController:
    """Tests for UserSessionController."""

    def test_validate_current_session_age_no_cat_claim(self):
        from oxutils.auth.exceptions import ForbidNewSession
        from oxutils.auth.sessions.controllers import UserSessionController

        ctrl = UserSessionController()
        request = Mock()
        request.user = Mock(spec=[])

        with pytest.raises(ForbidNewSession):
            ctrl._validate_current_session_age(request)
