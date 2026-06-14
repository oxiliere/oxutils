"""
Schemas for the invitations module.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ninja import ModelSchema, Schema
from pydantic import EmailStr, field_validator
from django.utils.translation import gettext_lazy as _

from oxutils.auth.invitations.models import BaseInvitation, InvitationRole, InvitationStatus


# ── Request schemas ────────────────────────────────────────────────

class CreateInvitationSchema(Schema):
    email: EmailStr
    role: str = InvitationRole.MEMBER
    message: str = ""

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in InvitationRole.values:
            raise ValueError(_("Invalid role. Must be one of: {}").format(
                ", ".join(InvitationRole.values)
            ))
        return v


class CancelInvitationSchema(Schema):
    token: str


class AcceptInvitationSchema(Schema):
    token: str


class ResendInvitationSchema(Schema):
    token: str


# ── Response schemas ───────────────────────────────────────────────

class InvitationOutSchema(ModelSchema):
    tenant_name: Optional[str] = None
    invited_by_email: Optional[str] = None
    invitee_email: Optional[str] = None

    class Meta:
        model = BaseInvitation
        fields = [
            "id", "email", "token", "status", "role",
            "expires_at", "accepted_at", "created_at", "message",
        ]

    @staticmethod
    def resolve_tenant_name(obj: BaseInvitation) -> str:
        return getattr(obj.tenant, "name", str(obj.tenant_id))

    @staticmethod
    def resolve_invited_by_email(obj: BaseInvitation) -> str:
        return getattr(obj.invited_by, "email", "")

    @staticmethod
    def resolve_invitee_email(obj: BaseInvitation) -> Optional[str]:
        return obj.invitee.email if obj.invitee else None


class InvitationListSchema(Schema):
    invitations: List[InvitationOutSchema]
    total: int


class InvitationResponseSchema(Schema):
    success: bool
    message: str
    invitation: Optional[InvitationOutSchema] = None


class ValidateTokenSchema(Schema):
    valid: bool
    email: Optional[str] = None
    tenant_name: Optional[str] = None
    role: Optional[str] = None
    message: Optional[str] = None
