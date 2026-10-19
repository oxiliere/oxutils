from typing import cast, Dict
from oxutils.auth.tokens.app_settings import RefreshToken
from oxutils.auth.tokens.models import (
    RefreshTokenWhitelistModel,
)
from ninja_jwt.exceptions import InvalidToken
from oxutils.auth.utils import is_email_verified




def create_user_token(user, request):
    refresh = RefreshToken.for_user(user, request=request)
    return cast(RefreshToken, refresh)


def refresh_token(token: str, context: Dict):
    refresh = RefreshToken(token)

    current = RefreshTokenWhitelistModel.objects.filter(
        jti=refresh.payload["jti"]
    ).first()
    if current is None:
        # Already rotated or revoked. It cannot authenticate anything anymore;
        # deleting the whole session here would turn a benign concurrent
        # refresh (multiple tabs, retries) into a logout.
        raise InvalidToken()

    if not current.enabled:
        is_email_verified(current.user, raise_exception=True)
        raise InvalidToken()

    context = dict(context or {})
    force = bool(context.pop("force", False))

    data = {"access": str(refresh.access_token)}

    refresh.set_jti()
    refresh.set_exp()
    refresh.set_iat()
    # A rotation is not a reauthentication: only ``rat`` may move, and only
    # when the caller explicitly re-proved the identity.
    if force:
        refresh.set_rat(force=True)

    data["refresh"] = str(refresh)

    # Rotate in place: ``created`` (session start), ``session`` and ``enabled``
    # stay untouched, and bypassing ``RefreshTokenManager.create()`` keeps the
    # rotation from counting as a new session (no eviction at the limit).
    for field, value in context.items():
        setattr(current, field, value)
    current.jti = refresh.payload["jti"]
    current.save()

    return data
