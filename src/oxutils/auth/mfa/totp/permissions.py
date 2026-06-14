from allauth.mfa.models import Authenticator
from allauth.mfa.utils import is_mfa_enabled
from django.http import HttpRequest
from ninja_extra import permissions

from oxutils.auth.exceptions import ReauthenticationRequired
from oxutils.auth.utils import did_recently_authenticate, populate_user


class IsMFAEnabled(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        populate_user(request)
        return is_mfa_enabled(request.user, [Authenticator.Type.TOTP])


class IsRecentAuthentication(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        populate_user(request)

        if request.user.is_anonymous or not did_recently_authenticate(request):
            raise ReauthenticationRequired()

        return True
