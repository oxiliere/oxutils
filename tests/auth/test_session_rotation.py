"""Session-stable refresh-token rotation.

Rotating a refresh token must not move the session's creation date, must not
count as a new session, and must not wipe the session when a stale token is
replayed by a concurrent request.
"""

import time
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from ninja_jwt.exceptions import InvalidToken

from oxutils.auth.tokens.app_settings import RefreshToken
from oxutils.auth.tokens.models import RefreshTokenWhitelistModel
from oxutils.auth.tokens.utils import refresh_token

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    User = get_user_model()
    user = User.objects.create_user(username="session-user", password="secret")
    # ``for_user`` stamps the role claim; the default User has no role field.
    user.role = "user"
    return user


def _open_session(user):
    token = RefreshToken.for_user(user)
    row = RefreshTokenWhitelistModel.objects.get(jti=token.payload["jti"])
    return token, row


def test_rotation_keeps_the_session_creation_date(user):
    token, row = _open_session(user)
    aged = timezone.now() - timedelta(days=10)
    RefreshTokenWhitelistModel.objects.filter(pk=row.pk).update(created=aged)

    data = refresh_token(str(token), context={})

    rotated = RefreshTokenWhitelistModel.objects.get(session=row.session)
    assert rotated.created == aged
    assert rotated.session == row.session
    assert rotated.enabled is True
    assert rotated.jti == RefreshToken(data["refresh"]).payload["jti"]
    assert rotated.jti != token.payload["jti"]


def test_rotation_keeps_the_session_creation_claim(user):
    token, _ = _open_session(user)

    data = refresh_token(str(token), context={})

    payload = RefreshToken(data["refresh"]).payload
    assert payload["cat"] == token.payload["cat"]
    assert payload["session"] == token.payload["session"]


def test_a_reauthentication_moves_only_the_recent_auth_claim(user):
    token, row = _open_session(user)
    aged = timezone.now() - timedelta(days=10)
    RefreshTokenWhitelistModel.objects.filter(pk=row.pk).update(created=aged)
    old_rat = int(time.time()) - 3600
    token.payload["rat"] = old_rat

    data = refresh_token(str(token), context={"force": True})

    payload = RefreshToken(data["refresh"]).payload
    assert payload["cat"] == token.payload["cat"]
    assert payload["rat"] > old_rat

    rotated = RefreshTokenWhitelistModel.objects.get(session=row.session)
    assert rotated.created == aged


def test_legacy_tokens_do_not_gain_a_recent_auth_claim_on_rotation(user):
    token, _ = _open_session(user)
    token.payload.pop("rat", None)

    data = refresh_token(str(token), context={})

    assert "rat" not in RefreshToken(data["refresh"]).payload


def test_rotation_does_not_evict_a_session_at_the_limit(user, settings):
    settings.JWT_ALL_AUTH_MAX_SESSIONS = 3
    tokens = [RefreshToken.for_user(user) for _ in range(3)]
    sessions = set(
        RefreshTokenWhitelistModel.objects.values_list("session", flat=True)
    )
    assert len(sessions) == 3

    refresh_token(str(tokens[0]), context={})

    assert (
        set(RefreshTokenWhitelistModel.objects.values_list("session", flat=True))
        == sessions
    )


def test_replaying_a_rotated_token_does_not_wipe_the_session(user):
    token, row = _open_session(user)
    refresh_token(str(token), context={})

    with pytest.raises(InvalidToken):
        refresh_token(str(token), context={})

    assert RefreshTokenWhitelistModel.objects.filter(session=row.session).exists()
