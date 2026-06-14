from django.utils.translation import gettext_lazy as _
from ninja.errors import HttpError

from allauth.mfa import app_settings
from allauth.mfa.adapter import get_adapter
from allauth.mfa.models import Authenticator

from oxutils.auth.mfa.recovery_codes import flows



class RecoveryCodeService:

    @staticmethod
    def generate_recovery_codes(request):
        """Generate new recovery codes for user"""
        if not flows.can_generate_recovery_codes(request.user):
            raise get_adapter().validation_error("cannot_generate_recovery_codes")

        authenticator = flows.generate_recovery_codes(request)
        codes = authenticator.wrap().get_unused_codes()

        return {
            "success": True,
            "message": _("Recovery codes generated successfully"),
            "codes": codes
        }

    @staticmethod
    def recovery_codes_status(request):
        """Get recovery codes status for user"""
        unused_codes = []
        authenticator = Authenticator.objects.filter(
            user__pk=request.user.pk, type=Authenticator.Type.RECOVERY_CODES
        ).first()

        if authenticator:
            unused_codes = authenticator.wrap().get_unused_codes()

        return {
            "is_active": bool(authenticator),
            "unused_codes": unused_codes,
            "total_count": app_settings.RECOVERY_CODE_COUNT
        }

    @staticmethod
    def download_recovery_codes(request):
        """Get recovery codes for download"""
        authenticator = flows.view_recovery_codes(request)
        if not authenticator:
            raise HttpError(404, "Recovery codes not found")

        unused_codes = authenticator.wrap().get_unused_codes()
        if not unused_codes:
            raise HttpError(404, "No unused recovery codes available")

        # Generate text content for download
        content_lines = [
            "# Recovery Codes",
            "# Keep these codes safe - they can be used to access your account if you lose your authenticator device.",
            "# Each code can only be used once.",
            "",
        ]

        for i, code in enumerate(unused_codes, 1):
            content_lines.append(f"{i:2d}. {code}")

        content_lines.extend([
            "",
            "# Generated on: " + authenticator.created_at.strftime("%Y-%m-%d %H:%M:%S") if authenticator.created_at else "Unknown",
            "# Total codes: " + str(len(unused_codes)),
        ])

        content = "\n".join(content_lines)

        return {
            "content": content,
            "filename": "oxi-recovery-codes.txt",
            "content_type": "text/plain"
        }
