from allauth.account import app_settings
from allauth.account.internal import flows
from allauth.account.internal.flows.email_verification import (
    send_verification_email_to_address,
)
from allauth.account.models import EmailAddress
from django.core.validators import validate_email
from django.forms import ValidationError
from django.http import HttpRequest


class UserEmailService:
    def get_user_emails(self, request: HttpRequest):
        return EmailAddress.objects.filter(user=request.user).order_by("email")

    def can_add_email(self, request: HttpRequest):
        return EmailAddress.objects.can_add_email(request.user)

    def add_email(self, request: HttpRequest, form):
        flows.manage_email.add_email(request, form)

    def set_primary(self, request: HttpRequest, email_address):
        return flows.manage_email.mark_as_primary(request, email_address)

    def send_verification_email(self, request: HttpRequest, email):
        email_address = self._get_email_address(request, email)
        did_send_verification_email = False

        if email_address:
            did_send_verification_email = send_verification_email_to_address(request, email_address)

        return app_settings.EMAIL_VERIFICATION_BY_CODE_ENABLED and did_send_verification_email

    def remove(self, request: HttpRequest, email):
        email_address = self._get_email_address(request, email)
        if email_address:
            return flows.manage_email.delete_email(request, email_address)
        return False

    def _get_email_address(self, request: HttpRequest, email):
        try:
            validate_email(email)
        except ValidationError:
            return None
        try:
            return EmailAddress.objects.get_for_user(user=request.user, email=email)
        except EmailAddress.DoesNotExist:
            pass

    def sync_user_email_address(self, request: HttpRequest):
        flows.manage_email.sync_user_email_address(request.user)
