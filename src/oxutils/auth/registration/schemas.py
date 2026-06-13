"""
Registration schemas – rewritten to use the invitations backend.
"""
import re
from typing import Any, Dict, Optional

from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.account.utils import setup_user_email
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.http import HttpRequest
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext_lazy as _
from ninja import Schema
from pydantic import EmailStr, field_validator, model_validator

from oxutils.auth.invitations.backend import invitation_backend
from oxutils.auth.invitations.models import Invitation


class RegisterSchema(Schema):
    """
    Schema for user registration.

    Supports two flows:
        1. Standard registration (no token)
        2. Invitation-based registration (with token)
    """
    email: EmailStr
    password1: str
    password2: str
    first_name: str
    last_name: str
    token: Optional[str] = None

    # ── Field validators ───────────────────────────────────────────

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, email: str, info) -> str:
        data = info.data if hasattr(info, "data") else {}
        # With token → invitation flow, lighter validation
        if data.get("token") is not None:
            return email.lower().strip()
        email = get_adapter().clean_email(email)
        return email

    @field_validator("password1")
    @classmethod
    def validate_password1(cls, password: str) -> str:
        try:
            return get_adapter().clean_password(password)
        except DjangoValidationError as djv_exc:
            raise ValueError(str(djv_exc))

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, first_name: str) -> str:
        pattern = r"^[A-Za-zÀ-ÖØ-öø-ÿ ]+$"
        if not re.match(pattern, first_name):
            raise ValueError(_("Incorrect name, please use only letters without spaces"))
        first_name = re.sub(" +", " ", first_name)
        return " ".join([txt.capitalize() for txt in first_name.split(" ")])

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, last_name: str) -> str:
        pattern = r"^[A-Za-zÀ-ÖØ-öø-ÿ ]+$"
        if not re.match(pattern, last_name):
            raise ValueError(_("Incorrect name, please use only letters without spaces"))
        last_name = re.sub(" +", " ", last_name)
        return " ".join([txt.capitalize() for txt in last_name.split(" ")])

    @model_validator(mode="after")
    def validate_passwords_match(self) -> "RegisterSchema":
        if not constant_time_compare(self.password1, self.password2):
            raise ValueError(_("The two password fields didn't match."))
        return self

    # ── Helpers ────────────────────────────────────────────────────

    def get_cleaned_data(self) -> Dict[str, Any]:
        return {
            "email": self.email,
            "password1": self.password1,
            "first_name": self.first_name,
            "last_name": self.last_name,
        }

    @property
    def cleaned_data(self):
        return self.get_cleaned_data()

    # ── Save flow ──────────────────────────────────────────────────

    @transaction.atomic
    def save(self, request: HttpRequest):
        """
        Create and save a new user.

        When a token is provided, validates the invitation and links
        the new user to the corresponding tenant.
        """
        adapter = get_adapter()
        User = get_user_model()
        user = User.objects.filter(email=self.email).first()
        invitation = None

        # ── Resolve invitation if token provided ───────────────────
        if self.token:
            invitation = invitation_backend.validate_token(self.token)
            if invitation is None:
                raise ValueError(_("The invitation link is invalid or has expired."))

        # ── Check existing user ────────────────────────────────────
        if user and user.is_active:
            raise ValueError(_("A user with this email already exists."))

        # ── Create or reuse user ───────────────────────────────────
        if user is None:
            user = adapter.new_user(request)
        # If user exists but is inactive (pre-created by invitation), reuse it

        user.first_name = self.first_name
        user.last_name = self.last_name
        user.email = self.email
        user.is_active = True
        user.set_password(self.password1)
        user.save()

        # ── Setup email ────────────────────────────────────────────
        setup_user_email(request, user, [])

        # ── Handle invitation ──────────────────────────────────────
        if invitation:
            # Accept the invitation (adds user to tenant)
            invitation_backend.accept_invitation(self.token, user)

            # Auto-confirm email for invited users
            email_obj = EmailAddress.objects.filter(user=user, email=user.email).first()
            if email_obj is not None:
                adapter.confirm_email(request, email_obj)
        else:
            # Standard registration: send verification email
            from oxutils.auth.emails.services import UserEmailService

            email_service = UserEmailService()
            request.user = user
            email_service.send_verification_email(request, user.email)

        return user

    def custom_signup(self, request: HttpRequest, user) -> None:
        """Override this method to add custom signup logic."""
        pass


# ── Ancillary schemas ──────────────────────────────────────────────

class VerifyEmailSchema(Schema):
    key: str


class RegisterResponseSchema(Schema):
    success: bool
    message: str
    email_verification_required: bool = False
