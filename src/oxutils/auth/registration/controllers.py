"""
Registration controllers – rewritten to use the invitations backend.
"""
from typing import Any, Dict

from allauth.account.utils import complete_signup
from allauth.account.views import ConfirmEmailView
from django.conf import settings
from django.db import transaction
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from ninja_extra import ControllerBase, http_get, http_post, status
from ninja_extra.permissions import AllowAny
from ninja_extra.throttling import AnonRateThrottle

from oxutils.auth.registration.schemas import (
    RegisterSchema,
    RegisterResponseSchema,
)
from oxutils.auth.tokens.app_settings import RefreshToken
from oxutils.auth.tokens.models import RefreshTokenWhitelistModel
from oxutils.auth.utils import get_user_agent, sensitive_post_parameters_m
from oxutils.mixins.schemas import ResponseSchema


class RegisterController(ControllerBase):
    """Controller for user registration (standard + invitation-based)."""

    @http_post(
        "/register",
        permissions=[AllowAny],
        auth=None,
        throttle=[AnonRateThrottle()],
        response={200: RegisterResponseSchema, 400: RegisterResponseSchema},
    )
    @get_user_agent
    @sensitive_post_parameters_m
    def register(self, request: HttpRequest, data: RegisterSchema) -> Dict[str, Any]:
        """Register a new user. Accepts an optional invitation token."""
        with transaction.atomic():
            user = data.save(request)
            email_verification = getattr(settings, "EMAIL_VERIFICATION", False)

            # Generate refresh token
            refresh = RefreshToken.for_user(
                user, request, enabled=not bool(email_verification)
            )

            # Complete signup process
            complete_signup(request, user, email_verification, None)

        if email_verification:
            return {
                "success": True,
                "message": str(_("Verification e-mail sent.")),
                "email_verification_required": True,
            }

        return {
            "success": True,
            "message": str(_("Registration successful.")),
            "email_verification_required": False,
        }


class EmailVerificationController(ControllerBase, ConfirmEmailView):
    """Controller for email verification."""

    @http_get(
        "/verify-email/{key}",
        permissions=[AllowAny],
        response={status.HTTP_200_OK: ResponseSchema, status.HTTP_404_NOT_FOUND: ResponseSchema},
        auth=None,
        throttle=[AnonRateThrottle()],
    )
    def verify_email(self, request: HttpRequest, key: str):
        """Verify email address using confirmation key."""
        self.kwargs = {"key": key}
        confirmation = self.get_object()

        # Enable refresh token
        refresh = RefreshTokenWhitelistModel.objects.filter(
            user=confirmation.email_address.user
        ).first()
        if refresh:
            refresh.enabled = True
            refresh.save()

        # Confirm the email
        confirmation.confirm(request)

        return {"code": "success", "detail": "successfully !"}
