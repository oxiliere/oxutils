from django.contrib.auth.models import update_last_login
from django.http import HttpRequest
from ninja_extra import (
    ControllerBase,
    api_controller,
    http_post,
)
from ninja_extra.permissions import IsAuthenticated
from ninja_jwt.exceptions import InvalidToken
from ninja_jwt.settings import api_settings

from oxutils.auth.mfa.totp.permissions import IsMFAEnabled
from oxutils.auth.mixins import CookieTokenMixin
from oxutils.auth.schemas import TokenObtainPairOutputSchema
from oxutils.auth.tokens.utils import (
    create_user_token,
    refresh_token,
)
from oxutils.auth.utils import (
    get_refresh_token,
    load_user,
    user_agent_dict,
    write_user_agent,
)

from .schemas import AuthenticateSchema, ReauthenticateSchema


@api_controller("/mfa", tags=["MFA"])
class MFAAuthenticateController(ControllerBase, CookieTokenMixin):
    def get_tokens(self, request: HttpRequest, reauthenticate=False):
        write_user_agent(request)

        if not reauthenticate:
            token = create_user_token(request.user, request)
            tokens = {"access": str(token.access_token), "refresh": str(token)}

            if api_settings.UPDATE_LAST_LOGIN:
                update_last_login(None, request.user)
        else:
            _refresh_token = get_refresh_token(request)

            if not _refresh_token:
                raise InvalidToken

            ctx = {"force": True, **user_agent_dict(request)}
            tokens = refresh_token(_refresh_token, context=ctx)

        self.set_token_cookie(access_token=tokens["access"], refresh_token=tokens["refresh"])

        return {"code": "logged_in", "access": tokens["access"], "refresh": tokens["refresh"]}

    @http_post("/authenticate", response=TokenObtainPairOutputSchema, auth=None)
    @load_user
    def authenticate(self, request: HttpRequest, payload: AuthenticateSchema):
        payload.authenticate()
        return self.get_tokens(request)

    @http_post(
        "/reauthenticate",
        response=TokenObtainPairOutputSchema,
        permissions=[IsAuthenticated & IsMFAEnabled()],
    )
    @load_user
    def reauthenticate(self, request: HttpRequest, payload: ReauthenticateSchema):
        payload.authenticate()
        return self.get_tokens(request)
