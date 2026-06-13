import base64

from allauth.mfa.adapter import get_adapter
from allauth.mfa.internal.flows.add import validate_can_add_authenticator
from allauth.mfa.models import Authenticator
from allauth.mfa.totp.internal import auth
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from ninja.errors import HttpError

from oxutils.auth.mfa.totp import flows

User = get_user_model()


class TOTPService:
    """Service for TOTP operations and validation"""

    @staticmethod
    def get_totp_secret(regenerate=False):
        """Get TOTP secret for user"""
        return auth.get_totp_secret(regenerate=regenerate)

    @staticmethod
    def validate_totp_activation(user, code, secret=None):
        """Validate TOTP activation code"""
        # Validate user can add authenticator
        validate_can_add_authenticator(user)

        # Get secret if not provided
        if secret is None:
            secret = auth.get_totp_secret(regenerate=False)

        # Validate TOTP code
        if not auth.validate_totp_code(secret, code):
            adapter = get_adapter()
            raise adapter.validation_error("incorrect_code")

        return True

    @staticmethod
    def validate_totp_deactivation(authenticator):
        """Validate TOTP deactivation"""
        adapter = get_adapter()
        if not adapter.can_delete_authenticator(authenticator):
            raise adapter.validation_error("cannot_delete_authenticator")

        return True

    @staticmethod
    def get_totp_secret_with_qr(request, payload):
        """Get TOTP secret and QR code for user"""
        # Validate user can add authenticator
        validate_can_add_authenticator(request.user)

        # Get or generate secret
        secret = auth.get_totp_secret(regenerate=payload.regenerate)

        # Build QR code
        adapter = get_adapter()
        totp_url = adapter.build_totp_url(request.user, secret)
        totp_svg = adapter.build_totp_svg(totp_url)
        base64_data = base64.b64encode(totp_svg.encode("utf8")).decode("utf-8")
        qr_code_url = f"data:image/svg+xml;base64,{base64_data}"

        return {
            "secret": secret,
            "qr_code_url": qr_code_url,
            "backup_codes": None,  # Will be generated during activation
        }

    @staticmethod
    def activate_totp(request, payload):
        """Activate TOTP for user (validation only)"""
        # Validate the TOTP code with the provided secret
        TOTPService.validate_totp_activation(request.user, payload.code, payload.secret)

        # Activate TOTP
        totp_auth, rc_auth = flows.activate_totp(request, payload)

        # Generate backup codes if recovery codes were created
        backup_codes = None
        if rc_auth:
            # Get the recovery codes that were just generated
            backup_codes = [code.code for code in rc_auth.data.get("codes", [])]

        return {
            "success": True,
            "message": str(_("TOTP activated successfully")),
            "secret": payload.secret,
            "backup_codes": backup_codes,
        }

    @staticmethod
    def deactivate_totp(request):
        """Deactivate TOTP for user"""

        try:
            # Get user's authenticator
            authenticator = Authenticator.objects.filter(
                user=request.user, type=Authenticator.Type.TOTP
            ).first()

            if not authenticator:
                raise HttpError(404, "TOTP authenticator not found")

            TOTPService.validate_totp_deactivation(authenticator)
            flows.deactivate_totp(request, authenticator)

        except Exception as e:
            raise HttpError(400, str(e))

        return {"success": True, "message": str(_("TOTP deactivated successfully"))}

    @staticmethod
    def totp_status(request):
        try:
            authenticator = Authenticator.objects.filter(
                user=request.user, type=Authenticator.Type.TOTP
            ).first()

            if authenticator:
                return {
                    "is_active": True,
                    "created_at": authenticator.created_at.isoformat()
                    if authenticator.created_at
                    else None,
                    "last_used_at": authenticator.last_used_at.isoformat()
                    if authenticator.last_used_at
                    else None,
                }
            else:
                return {"is_active": False, "created_at": None, "last_used_at": None}
        except Exception as e:
            raise HttpError(400, str(e))
