from typing import Optional

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from ninja_extra import ControllerBase, api_controller, http_post
from ninja_extra.permissions import IsAuthenticated
from ninja_extra.throttling import AnonRateThrottle, UserRateThrottle
from ninja_jwt.exceptions import InvalidToken, TokenError
from ninja_jwt.schema_control import SchemaControl
from ninja_jwt.settings import api_settings

from oxutils.auth.invitations.controllers import InvitationController
from oxutils.auth.mixins import CookieTokenMixin
from oxutils.auth.signals import user_logged_in, user_logged_out
from oxutils.auth.password_reset.controllers import (
    PasswordResetConfirmController,
    PasswordResetController,
    ResetNewPasswordController,
)
from oxutils.auth.registration.controllers import (
    EmailVerificationController,
    RegisterController,
)
from oxutils.auth.schemas import (
    LoginSchema,
    PasswordChangeResponseSchema,
    PasswordChangeSchema,
    ReauthenticatePasswordSchema,
    RemoveRefreshTokenSchema,
    SendVerificationEmailSchema,
    TokenObtainMFARequiredSchema,
    TokenObtainPairOutputSchema,
    TokenRefreshInputSchema,
    TokenRefreshOutputSchema,
    TokenRefreshSchema,
)
from oxutils.auth.utils import (
    get_refresh_token,
    get_user_agent,
    load_user,
    sensitive_post_parameters_m,
    user_agent_dict,
)
from oxutils.exceptions import ExceptionCode
from oxutils.mixins.schemas import ResponseSchema

schema = SchemaControl(api_settings)


class LoginController(ControllerBase, CookieTokenMixin):
    auto_import = False

    @http_post(
        "/login",
        response={200: TokenObtainPairOutputSchema, 202: TokenObtainMFARequiredSchema},
        url_name="token_obtain_pair",
        operation_id="token_obtain_pair",
        throttle=[AnonRateThrottle()],
        auth=None,
    )
    def obtain_token(self, request: HttpRequest, user_token: LoginSchema):
        user_token.check_user_authentication_rule()
        schema = user_token.to_response_schema()

        if schema.is_mfa_required():
            return 202, schema

        self.set_token_cookie(access_token=schema.access, refresh_token=schema.refresh)

        user_logged_in.send_robust(sender=self.__class__, request=request, user=user_token._user)

        return schema

    @http_post(
        "/verify-email",
        response={
            200: ResponseSchema,
        },
        throttle=[AnonRateThrottle()],
        auth=None,
    )
    def send_verification_email(self, request: HttpRequest, payload: SendVerificationEmailSchema):
        payload.send_verification_email(request)

        return ResponseSchema(
            code=ExceptionCode.SUCCESS, detail=str(_("Verification email sent successfully."))
        )


class ReauthenticateController(ControllerBase, CookieTokenMixin):
    auto_import = False

    @http_post(
        "/reauthenticate",
        response={
            200: TokenObtainPairOutputSchema,
        },
        url_name="reauthenticate_password",
        operation_id="reauthenticate_password",
        throttle=[UserRateThrottle()],
        permissions=[IsAuthenticated],
    )
    @load_user
    def reauthenticate(self, request: HttpRequest, payload: ReauthenticatePasswordSchema):
        schema = payload.authenticate(request)

        self.set_token_cookie(access_token=schema.access, refresh_token=schema.refresh)

        user_logged_in.send_robust(sender=self.__class__, request=request, user=request.user)

        return schema


class LogoutController(ControllerBase, CookieTokenMixin):
    """
    Calls Django logout method and delete the Token object
    assigned to the current User object.

    Accepts/Returns nothing.
    """

    @http_post("/logout", permissions=[IsAuthenticated], response={200: dict, 401: dict})
    def logout(self, request: HttpRequest):
        input_data = {"user": request.user.id}

        refresh_token = get_refresh_token(request)

        if not refresh_token:
            raise InvalidToken

        input_data["refresh"] = refresh_token

        try:
            RemoveRefreshTokenSchema.model_validate(input_data, context={"user": request.user.id})
            self.remove_token_cookie()
            user_logged_out.send_robust(sender=self.__class__, request=request, user=request.user)
            return 200, {"detail": _("Successfully logged out.")}
        except (TokenError, InvalidToken) as exc:
            return 401, {"detail": _("Invalid token.")}


class PasswordChangeController(ControllerBase):
    @http_post(
        "/change_password",
        permissions=[IsAuthenticated],
        throttle=[UserRateThrottle()],
        response=PasswordChangeResponseSchema,
    )
    @sensitive_post_parameters_m
    @load_user
    def change_user_password(self, request: HttpRequest, payload: PasswordChangeSchema):
        return payload.get_response(request)


class TokenRefreshController(ControllerBase, CookieTokenMixin):
    @http_post(
        "/refresh",
        auth=None,
        response={200: TokenRefreshOutputSchema, 401: dict},
        url_name="token_refresh",
        operation_id="token_refresh",
        throttle=[AnonRateThrottle()],
    )
    @get_user_agent
    def refresh_token(self, request: HttpRequest, payload: Optional[TokenRefreshInputSchema]):
        try:
            input_data = {}
            refresh_token = get_refresh_token(request)

            if not refresh_token:
                if payload.refresh is None:
                    raise InvalidToken

                refresh_token = payload.refresh

            input_data["refresh"] = refresh_token
            ctx = user_agent_dict(request)
            tokens = TokenRefreshSchema.model_validate(input_data, context=ctx)

            self.set_token_cookie(access_token=tokens["access"], refresh_token=tokens["refresh"])

            return tokens
        except (TokenError, InvalidToken) as exc:
            return 401, {"detail": _("Invalid token.")}


@api_controller(
    "/auth",
)
class AuthController(
    LoginController,
    ReauthenticateController,
    LogoutController,
    PasswordChangeController,
    TokenRefreshController,
    EmailVerificationController,
    RegisterController,
    InvitationController,
    PasswordResetConfirmController,
    PasswordResetController,
    ResetNewPasswordController,
):
    pass
