from django.http import HttpRequest
from ninja_extra.permissions import BasePermission as DefaultBasePermission
from ninja_jwt.exceptions import TokenError

from oxutils.auth.constants import (
    FOR_USER,
    ONE_TIME_PERMISSION,
    PASS_RESET_ACCESS,
    PASS_RESET_COOKIE,
)
from oxutils.auth.password_reset.models import SetPasswordTokenUser
from oxutils.auth.tokens.app_settings import RefreshToken


class ResetPasswordPermission(DefaultBasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        if bool(request.user and request.user.is_authenticated):
            return False

        if hasattr(request, "COOKIES") and PASS_RESET_COOKIE in request.COOKIES:
            access_token = request.COOKIES.get(PASS_RESET_COOKIE)
            try:
                access_token = RefreshToken.access_token_class(access_token)
            except TokenError as exc:
                return False
            if access_token and ONE_TIME_PERMISSION in access_token and FOR_USER in access_token:
                if access_token[ONE_TIME_PERMISSION] == PASS_RESET_ACCESS:
                    request.user = SetPasswordTokenUser(access_token)
                    request.auth = access_token
                    return True
        return False
