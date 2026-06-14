from django.http import HttpRequest, HttpResponse
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import IsAuthenticated

from oxutils.auth.utils import load_user

from .schemas import (
    RecoveryCodesGenerateResponseSchema,
    RecoveryCodesGenerateSchema,
    RecoveryCodesStatusResponseSchema,
)
from .services import RecoveryCodeService


@api_controller("/mfa/recovery-codes", permissions=[IsAuthenticated], tags=["MFA"])
class RecoveryCodeController(ControllerBase):
    @route.post("/generate", response=RecoveryCodesGenerateResponseSchema)
    def generate_recovery_codes(self, request: HttpRequest, payload: RecoveryCodesGenerateSchema):
        """Generate new recovery codes for user"""
        return RecoveryCodeService.generate_recovery_codes(request)

    @route.get("/status", response=RecoveryCodesStatusResponseSchema)
    def get_recovery_codes_status(self, request: HttpRequest):
        """Get recovery codes status for user"""
        return RecoveryCodeService.recovery_codes_status(request)

    @route.get("/download")
    @load_user
    def download_recovery_codes(self, request: HttpRequest):
        """Download recovery codes as text file"""
        result = RecoveryCodeService.download_recovery_codes(request)

        # Create HTTP response with file download
        response = HttpResponse(result["content"], content_type=result["content_type"])
        response["Content-Disposition"] = f'attachment; filename="{result["filename"]}"'
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"

        return response
