"""
Tests for oxutils.auth.sessions module.
"""

from datetime import timedelta
from unittest.mock import Mock

import pytest
from django.utils import timezone
from ninja_jwt.utils import datetime_to_epoch


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


class TestSessionAgeGuard:
    """The 3-day guard reads the session's creation time, not the token's."""

    @staticmethod
    def _request(cat):
        from oxutils.jwt.models import TokenUser

        request = Mock()
        request.user = TokenUser({"cat": datetime_to_epoch(cat), "sub": "1"})
        return request

    def test_a_session_older_than_three_days_may_revoke(self):
        from oxutils.auth.sessions.controllers import UserSessionController

        request = self._request(timezone.now() - timedelta(days=4))

        # Must not raise.
        UserSessionController()._validate_current_session_age(request)

    def test_a_fresh_session_may_not_revoke(self):
        from oxutils.auth.exceptions import ForbidNewSession
        from oxutils.auth.sessions.controllers import UserSessionController

        request = self._request(timezone.now() - timedelta(days=1))

        with pytest.raises(ForbidNewSession):
            UserSessionController()._validate_current_session_age(request)
