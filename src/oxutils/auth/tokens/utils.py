from typing import cast, Dict
from django.utils import timezone
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

    query_set = list(RefreshTokenWhitelistModel.objects.filter(jti=refresh.payload["jti"]).all())
    if len(query_set) == 0:
        # Suspicious operation
        RefreshTokenWhitelistModel.objects.filter(session=refresh.payload["session"]).delete()
        raise InvalidToken()
    if not query_set[0].enabled:
        is_email_verified(query_set[0].user, raise_exception=True)
        raise InvalidToken()

    data = {"access": str(refresh.access_token)}

    RefreshTokenWhitelistModel.objects.filter(jti=refresh.payload["jti"]).delete()

    refresh.set_jti()
    refresh.set_exp()
    refresh.set_iat()
    refresh.set_cat(force=bool(context.pop('force', False)))

    data["refresh"] = str(refresh)

    serializer_data = {
        'jti': refresh.payload['jti'],
        'user_id': refresh.payload['user_id'],
        'session': refresh.payload['session'],
        'created': timezone.now(),
        **context
    }

    RefreshTokenWhitelistModel.objects.create(
        **serializer_data
    )

    return data
