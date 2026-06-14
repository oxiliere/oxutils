from typing import List

from allauth.account import app_settings
from allauth.account.adapter import get_adapter
from allauth.account.internal import flows
from allauth.account.models import EmailAddress
from allauth.account.utils import (
    filter_users_by_email,
)
from allauth.core.internal.cryptokit import compare_user_code
from django.utils.translation import gettext_lazy as _
from ninja import ModelSchema, Schema
from pydantic import EmailStr, ValidationInfo, field_validator


class EmailAddressSchema(ModelSchema):
    class Meta:
        model = EmailAddress
        fields = "__all__"


class StatusEmailAddressSchema(Schema):
    can_add: bool
    emails: List[EmailAddressSchema]


class AddEmailSchema(Schema):
    email: EmailStr

    @field_validator("email")
    def clean_email(cls, v: str, info: ValidationInfo):
        value = v.lower()
        adapter = get_adapter()
        value = adapter.clean_email(value)
        users = filter_users_by_email(value)
        user = info.context["request"].user
        on_this_account = [u for u in users if u.pk == user.pk]
        on_diff_account = [u for u in users if u.pk != user.pk]

        if on_this_account:
            raise adapter.validation_error("duplicate_email")
        if (
            # Email is taken by a different account...
            on_diff_account
            # We care about not having duplicate emails
            and app_settings.UNIQUE_EMAIL
            # Enumeration prevention is turned off.
            and (not app_settings.PREVENT_ENUMERATION)
        ):
            raise adapter.validation_error("email_taken")
        if not EmailAddress.objects.can_add_email(user):
            raise adapter.validation_error("max_email_addresses", app_settings.MAX_EMAIL_ADDRESSES)

        return value

    def save(self, request):
        from allauth.account import signals

        if app_settings.EMAIL_VERIFICATION_BY_CODE_ENABLED:
            email_address = EmailAddress(user=request.user, email=self.email)
            flows.email_verification.send_verification_email_to_address(request, email_address)
            return email_address
        elif app_settings.CHANGE_EMAIL:
            return EmailAddress.objects.add_new_email(request, request.user, self.email)

        signals._add_email.send(
            sender=request.user.__class__,
            email=self.email,
            user=request.user,
        )

        return EmailAddress.objects.add_email(request, request.user, self.email, confirm=True)


class ConfirmEmailSchema(Schema):
    code: str
    email: EmailStr

    def clean_code(self):
        if not compare_user_code(actual=self.code, expected=self.code):
            raise get_adapter().validation_error("incorrect_code")
        return self.code
