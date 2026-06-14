from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from ninja_extra import ControllerBase, http_get, http_post, status
from ninja_extra.permissions import AllowAny
from ninja_extra.throttling import AnonRateThrottle, UserRateThrottle
from ninja_jwt.exceptions import InvalidToken

from oxutils.auth.constants import (
    FOR_USER,
    ONE_TIME_PERMISSION,
    PASS_RESET,
    PASS_RESET_ACCESS,
    PASS_RESET_COOKIE,
    PASSWORD_RESET_REDIRECT,
    REFRESH_TOKEN_COOKIE,
)
from oxutils.auth.password_reset.permissions import ResetPasswordPermission
from oxutils.auth.password_reset.schemas import (
    PasswordResetSchema,
    SetPasswordSchema,
)
from oxutils.auth.tokens.app_settings import RefreshToken
from oxutils.auth.tokens.models import GenericTokenModel, RefreshTokenWhitelistModel
from oxutils.auth.tokens.tokens import GenericToken
from oxutils.auth.utils import get_user_agent, sensitive_post_parameters_m


class PasswordResetController(ControllerBase):
    """
    Calls Django Auth PasswordResetForm save method.

    Accepts the following POST parameters: email
    Returns the success/fail message.
    """

    @http_post(
        "/password_reset",
        permissions=[
            AllowAny,
        ],
        throttle=[AnonRateThrottle()],
        auth=None,
        response=dict,
    )
    @get_user_agent
    def password_reset(self, request: HttpRequest, payload: PasswordResetSchema):
        payload.send_password_reset_email(request)
        return (
            status.HTTP_200_OK,
            {"detail": _("Password reset e-mail has been sent.")},
        )


class PasswordResetConfirmController(ControllerBase):
    form_url = getattr(settings, PASSWORD_RESET_REDIRECT, None)

    @http_get(
        "password_reset/confirm/{uidb64}/{token}",
        permissions=[
            AllowAny,
        ],
        throttle=[AnonRateThrottle()],
        auth=None,
        response={200: dict, 400: dict},
    )
    @get_user_agent
    def confirm_reset_password(self, request: HttpRequest, uidb64: str, token: str):
        user = self.get_user(uidb64)

        if user is not None:
            if GenericToken(request=request, purpose=PASS_RESET).check_token(user, token):
                refresh_token = RefreshToken()
                refresh_token[FOR_USER] = str(user.id)
                refresh_token[ONE_TIME_PERMISSION] = PASS_RESET_ACCESS
                access_token = refresh_token.access_token

                self.context.response.set_cookie(
                    key=PASS_RESET_COOKIE,
                    value=str(access_token),
                    httponly=getattr(settings, "PASSWORD_RESET_COOKIE_HTTP_ONLY", True),
                    secure=getattr(settings, "PASSWORD_RESET_COOKIE_SECURE", not settings.DEBUG),
                    samesite=getattr(settings, "PASSWORD_RESET_COOKIE_SAME_SITE", "Lax"),
                    domain=getattr(settings, "OXI_COOKIE_DOMAIN", None),
                    max_age=getattr(settings, "PASSWORD_RESET_COOKIE_MAX_AGE", 3600),
                )

                generic_token = GenericTokenModel(
                    **{
                        "token": access_token["jti"],
                        "user_id": user.id,
                        "purpose": PASS_RESET_ACCESS,
                    }
                )
                generic_token.save()

                return 200, {"validlink": True}
        return 400, {"validlink": False}

    @staticmethod
    def get_user(uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_user_model()._default_manager.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            get_user_model().DoesNotExist,
            ValidationError,
        ):
            user = None
        return user


class ResetNewPasswordController(ControllerBase):
    """
    Calls Django Auth SetPasswordForm save method.

    Accepts the following POST parameters: new_password1, new_password2
    Returns the success/fail message.
    """

    @http_post(
        "/password_reset/set-new",
        throttle=[UserRateThrottle()],
        permissions=(ResetPasswordPermission,),
        auth=None,
        response=dict,
    )
    @sensitive_post_parameters_m
    def set_new_password(self, request: HttpRequest, payload: SetPasswordSchema):
        # check the token has not been used
        query_set = GenericTokenModel.objects.filter(
            token=request.auth["jti"], purpose=PASS_RESET_ACCESS
        )
        if len(query_set) != 1:
            raise InvalidToken()
        query_set.delete()  # single use

        request.user = get_user_model().objects.get(id=request.user.id)

        # Revoke old sessions
        if getattr(settings, "LOGOUT_ON_PASSWORD_CHANGE", True):
            RefreshTokenWhitelistModel.objects.filter(user__pk=request.user.id).delete()

        refresh_token = RefreshToken.for_user(request.user)
        response_data = {"access": str(refresh_token.access_token), "detail": _("Password reset.")}

        # Handle refresh token based on configuration
        if not getattr(settings, "JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE", True):
            response_data["refresh"] = str(refresh_token)

        if getattr(settings, "JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE", True):
            self.context.response.set_cookie(
                key=REFRESH_TOKEN_COOKIE,
                value=str(refresh_token),
                httponly=True,
                secure=not settings.DEBUG if hasattr(settings, "DEBUG") else True,
                samesite="Lax",
            )

        return response_data
