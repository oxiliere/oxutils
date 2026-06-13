from typing import Any, Dict

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.sites.requests import RequestSite
from django.http import HttpRequest
from ninja import Schema
from ninja_extra import exceptions
from pydantic import EmailStr, field_validator

from oxutils.auth.constants import PASS_RESET
from oxutils.auth.schemas import BaseChangePasswordSchema
from oxutils.auth.tokens.tokens import GenericToken
from oxutils.auth.utils import get_template_path


class PasswordResetSchema(Schema):
    """
    Schema for requesting a password reset e-mail.
    """

    email: EmailStr

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return value.strip().lower()

    def get_email_options(self) -> Dict[str, Any]:
        """Override this method to change default e-mail options"""
        return {}

    def send_password_reset_email(self, request: HttpRequest) -> None:
        """Send password reset email."""
        # Create PasswordResetForm with the email data
        form_data = {"email": self.email}
        reset_form = PasswordResetForm(data=form_data)

        if not reset_form.is_valid():
            raise exceptions.ValidationError(reset_form.errors)

        opts = {
            "use_https": request.is_secure(),
            "from_email": settings.DEFAULT_FROM_EMAIL,
            "request": request,
            "domain_override": RequestSite(request).domain,
            "token_generator": GenericToken(request=request, purpose=PASS_RESET),
            "subject_template_name": get_template_path(
                "PASS_RESET_SUBJECT", "email/password/reset_email_subject.txt"
            ),
            "email_template_name": get_template_path(
                "PASS_RESET_EMAIL_TEXT", "email/password/reset_email_message.txt"
            ),
            "html_email_template_name": get_template_path(
                "PASS_RESET_EMAIL", "email/password/reset_email_message.html"
            ),
        }

        opts.update(self.get_email_options())

        # Check if the email is verified
        if EmailAddress.objects.filter(email=self.email, verified=True).count() > 0:
            reset_form.save(**opts)


class SetPasswordSchema(BaseChangePasswordSchema):
    """Schema for setting a new password (without requiring old password)."""

    @property
    def old_password_field_enabled(self):
        return False

    @property
    def logout_on_password_change(self):
        return False


class PasswordResetResponseSchema(Schema):
    """Schema for password reset response."""

    success: bool
    message: str
