from typing import List

from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from ninja.errors import HttpError
from ninja_extra import (
    ControllerBase,
    api_controller,
    http_delete,
    http_get,
    http_post,
    http_put,
)
from ninja_extra.permissions import IsAuthenticated
from ninja_extra.throttling import UserRateThrottle

from oxutils.auth.utils import load_user
from oxutils.exceptions import ExceptionCode, NinjaException, NotFoundException, ValidationException
from oxutils.mixins.schemas import ResponseSchema

from .schemas import (
    AddEmailSchema,
    EmailAddressSchema,
    StatusEmailAddressSchema,
)
from .services import UserEmailService


class EmailAddThrottle(UserRateThrottle):
    """Rate limiting for adding new email addresses"""

    scope = "email_add"
    rate = "5/hour"  # 5 emails per hour


class EmailVerificationThrottle(UserRateThrottle):
    """Rate limiting for sending verification emails"""

    scope = "email_verification"
    rate = "10/hour"  # 10 verification emails per hour


class EmailModificationThrottle(UserRateThrottle):
    """Rate limiting for email modifications (primary, delete)"""

    scope = "email_modification"
    rate = "20/hour"  # 20 modifications per hour


@api_controller("/emails", permissions=[IsAuthenticated], tags=["Emails"])
class EmailController(ControllerBase):
    """
    Controller for managing user email addresses
    """

    def __init__(self):
        self.email_service = UserEmailService()

    @http_get("", response=StatusEmailAddressSchema)
    @load_user
    def get_user_emails(self, request: HttpRequest):
        """
        Get all email addresses for the current user
        """
        self.email_service.sync_user_email_address(request)

        return {
            "can_add": self.email_service.can_add_email(request),
            "emails": self.email_service.get_user_emails(request),
        }

    @http_post("", response=EmailAddressSchema, throttle=[EmailAddThrottle()])
    @load_user
    def add_email(self, request: HttpRequest, payload: AddEmailSchema):
        """
        Add a new email address to the user's account
        """

        self.email_service.sync_user_email_address(request)
        try:
            # Use the service to add the email
            self.email_service.add_email(request, payload)

            # Return the created email address
            email_address = EmailAddress.objects.get_for_user(
                user=request.user, email=payload.email
            )

            return email_address

        except ImmediateHttpResponse as e:
            # Handle allauth validation errors
            raise HttpError(400, str(e)) from e
        except ValidationError as e:
            # Handle Django validation errors
            raise HttpError(400, str(e)) from e
        except Exception as e:
            # Handle any other errors
            raise HttpError(500, str(_("unknown error occurred"))) from e

    @http_put("/{email}/primary", response=ResponseSchema, throttle=[EmailModificationThrottle()])
    @load_user
    def set_primary_email(self, request: HttpRequest, email: str):
        """
        Set an email address as primary
        """
        self.email_service.sync_user_email_address(request)
        try:
            email_address = EmailAddress.objects.get_for_user(user=request.user, email=email)

            success = self.email_service.set_primary(request, email_address)

            if success:
                return ResponseSchema(
                    code=ExceptionCode.SUCCESS, detail=str(_("Email set as primary successfully."))
                )
            else:
                return ResponseSchema(
                    code=ExceptionCode.FAILED_ERROR,
                    detail=str(_("Impossible to set this email as primary.")),
                )

        except EmailAddress.DoesNotExist:
            raise NotFoundException(detail=str(_("Adresse email non trouvée."))) from e
        except Exception as e:
            raise NinjaException(code=500, detail=str(_("unknown error occurred"))) from e

    @http_post("/{email}/verify", response=ResponseSchema, throttle=[EmailVerificationThrottle()])
    @load_user
    def send_verification_email(self, request: HttpRequest, email: str):
        """
        Send verification email to the specified address
        """
        self.email_service.sync_user_email_address(request)

        sent = self.email_service.send_verification_email(request, email)

        if sent:
            return ResponseSchema(
                code=ExceptionCode.SUCCESS, detail=str(_("Verification email sent successfully."))
            )
        else:
            raise ValidationException(detail=str(_("Impossible to send verification email.")))

    @http_delete("/{email}", response=ResponseSchema, throttle=[EmailModificationThrottle()])
    @load_user
    def remove_email(self, request: HttpRequest, email: str):
        """
        Remove an email address from the user's account
        """
        self.email_service.sync_user_email_address(request)

        try:
            success = self.email_service.remove(request, email)

            if success:
                return ResponseSchema(
                    code=ExceptionCode.SUCCESS, detail=str(_("Email removed successfully."))
                )
            else:
                raise ValidationException(detail=str(_("Impossible to remove this email.")))

        except Exception as e:
            raise NinjaException(code=500, detail=str(_("unknown error occurred"))) from e
