from django.http import HttpRequest
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import IsAuthenticated

from oxutils.auth.utils import load_user

from .permissions import IsMFAEnabled, IsRecentAuthentication
from .schemas import (
    ActivateTOTPSchema,
    TOTPActivationResponseSchema,
    TOTPDeactivationResponseSchema,
    TOTPSecretRequestSchema,
    TOTPSecretResponseSchema,
    TOTPStatusResponseSchema,
)
from .services import TOTPService


@api_controller("/mfa/totp", permissions=[IsAuthenticated], tags=["MFA"])
class TOTPController(ControllerBase):
    @route.post("/secret", response=TOTPSecretResponseSchema, permissions=[IsAuthenticated])
    @load_user
    def get_totp_secret(self, request: HttpRequest, payload: TOTPSecretRequestSchema):
        """Get TOTP secret and QR code for user"""
        return TOTPService.get_totp_secret_with_qr(request, payload)

    @route.post(
        "/activate",
        response=TOTPActivationResponseSchema,
        permissions=[IsAuthenticated & IsRecentAuthentication()],
    )
    @load_user
    def activate_totp(self, request: HttpRequest, payload: ActivateTOTPSchema):
        """Activate TOTP for user (validation only)"""
        return TOTPService.activate_totp(request, payload)

    @route.post(
        "/deactivate",
        response=TOTPDeactivationResponseSchema,
        permissions=[IsAuthenticated & IsMFAEnabled() & IsRecentAuthentication()],
    )
    def deactivate_totp(self, request: HttpRequest):
        """Deactivate TOTP for user"""
        return TOTPService.deactivate_totp(request)

    @route.get("/status", response=TOTPStatusResponseSchema)
    @load_user
    def get_totp_status(self, request: HttpRequest):
        """Get TOTP status for user"""
        return TOTPService.totp_status(request)
