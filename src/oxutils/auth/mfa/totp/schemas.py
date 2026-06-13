from ninja import Schema
from typing import Optional
from pydantic import field_validator, Field
from django.utils.translation import gettext_lazy as _





class ActivateTOTPSchema(Schema):
    code: str = Field(..., min_length=6, max_length=8, description="TOTP code from authenticator app")
    secret: str = Field(..., description="The generated secret")
    
    @field_validator('code', mode='after')
    def validate_code_format(cls, v):
        """Validate code format"""

        if not v.isdigit():
            raise ValueError(_("Code must contain only digits"))

        return v


class TOTPSecretRequestSchema(Schema):
    """Schema for requesting TOTP secret"""
    regenerate: bool = Field(default=False, description="Whether to regenerate the secret")


class TOTPSecretResponseSchema(Schema):
    secret: str
    qr_code_url: str
    backup_codes: Optional[list[str]] = None


class TOTPActivationResponseSchema(Schema):
    success: bool
    message: str
    secret: Optional[str] = None
    backup_codes: Optional[list[str]] = None


class TOTPDeactivationResponseSchema(Schema):
    success: bool
    message: str


class TOTPStatusResponseSchema(Schema):
    """Schema for TOTP status"""
    is_active: bool
    created_at: Optional[str] = None
    last_used_at: Optional[str] = None