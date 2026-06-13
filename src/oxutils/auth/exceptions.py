from django.utils.translation import gettext_lazy as _
from ninja_extra import exceptions, status
from ninja_jwt.exceptions import AuthenticationFailed

from oxutils.mixins.base import DetailDictMixin


class NotVerifiedEmail(AuthenticationFailed):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("User email is not verified")
    default_code = "email_not_verified"


class IncorrectCredentials(AuthenticationFailed):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("Incorrect credentials")
    default_code = "incorrect_credentials"


class ForbidNewSession(DetailDictMixin, exceptions.APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = _("New session can't make this operations")
    default_code = "forbid_new_session"


class ReauthenticationRequired(DetailDictMixin, exceptions.APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = _("New session can't make this operations")
    default_code = "reauthentication_required"
