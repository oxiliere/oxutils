"""
Controllers for the invitations module.
"""

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from ninja_extra import (
    ControllerBase,
    api_controller,
    http_get,
    http_post,
)
from ninja_extra.pagination import (
    PageNumberPaginationExtra,
    PaginatedResponseSchema,
    paginate,
)
from ninja_extra.permissions import IsAuthenticated
from ninja_extra.throttling import AnonRateThrottle, UserRateThrottle

from oxutils.auth.invitations.backend import invitation_backend
from oxutils.auth.invitations.models import InvitationStatus, get_invitation_model
from oxutils.auth.invitations.schemas import (
    AcceptInvitationSchema,
    CancelInvitationSchema,
    CreateInvitationSchema,
    InvitationListSchema,
    InvitationOutSchema,
    InvitationResponseSchema,
    ResendInvitationSchema,
    ValidateTokenSchema,
)
from oxutils.auth.signals import invitation_resent
from oxutils.auth.utils import load_user
from oxutils.exceptions import ExceptionCode
from oxutils.mixins.schemas import ResponseSchema


class InvitationThrottle(UserRateThrottle):
    scope = "invitations"
    rate = "30/hour"


@api_controller("/invitations", permissions=[IsAuthenticated], tags=["Invitations"])
class InvitationController(ControllerBase):
    """
    API endpoints for managing tenant invitations.
    """

    # ── Create invitation ──────────────────────────────────────────

    @http_post("", response=InvitationResponseSchema, throttle=[InvitationThrottle()])
    @load_user
    def create_invitation(self, request: HttpRequest, payload: CreateInvitationSchema):
        """
        Invite a user by email to join a tenant.
        The tenant is determined from the current request context.
        """
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return self.respond_error(_("No tenant context found."))

        # Verify the inviter has permission to assign the requested role
        error = self._check_invite_permission(request.user, tenant, payload.role)
        if error:
            return self.respond_error(error)

        try:
            invitation = invitation_backend.create_invitation(
                tenant=tenant,
                email=payload.email,
                invited_by=request.user,
                role=payload.role,
                message=payload.message,
            )
        except ValueError as e:
            return self.respond_error(str(e))

        return InvitationResponseSchema(
            success=True,
            message=_("Invitation sent to {}").format(payload.email),
            invitation=InvitationOutSchema.from_orm(invitation),
        )

    # ── Accept invitation ──────────────────────────────────────────

    @http_post(
        "/accept",
        response=ResponseSchema,
        auth=None,
        throttle=[InvitationThrottle()],
    )
    @load_user
    def accept_invitation(self, request: HttpRequest, payload: AcceptInvitationSchema):
        """Accept an invitation using a token."""
        try:
            invitation_backend.accept_invitation(payload.token, request.user)
        except ValueError as e:
            return ResponseSchema(
                code=ExceptionCode.FAILED_ERROR,
                detail=str(e),
            )

        return ResponseSchema(
            code=ExceptionCode.SUCCESS,
            detail=_("Invitation accepted successfully."),
        )

    # ── Cancel invitation ──────────────────────────────────────────

    @http_post("/cancel", response=ResponseSchema, throttle=[InvitationThrottle()])
    @load_user
    def cancel_invitation(self, request: HttpRequest, payload: CancelInvitationSchema):
        """Cancel a pending invitation."""
        try:
            invitation_backend.cancel_invitation(payload.token, request.user)
        except ValueError as e:
            return ResponseSchema(
                code=ExceptionCode.FAILED_ERROR,
                detail=str(e),
            )

        return ResponseSchema(
            code=ExceptionCode.SUCCESS,
            detail=_("Invitation cancelled successfully."),
        )

    # ── List user invitations ──────────────────────────────────────

    @http_get("", response=PaginatedResponseSchema[InvitationOutSchema])
    @paginate(PageNumberPaginationExtra, page_size=20)
    @load_user
    def list_user_invitations(self, request: HttpRequest):
        """List pending invitations for the current user (paginated)."""
        return invitation_backend.get_user_invitations(request.user)

    # ── List tenant invitations ────────────────────────────────────

    @http_get("/tenant", response=PaginatedResponseSchema[InvitationOutSchema])
    @paginate(PageNumberPaginationExtra, page_size=20)
    @load_user
    def list_tenant_invitations(self, request: HttpRequest):
        """List invitations for the current tenant (paginated)."""
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return get_invitation_model().objects.none()

        return invitation_backend.get_tenant_invitations(tenant)

    # ── Validate token ─────────────────────────────────────────────

    @http_get(
        "/validate/{token}", response=ValidateTokenSchema, auth=None, throttle=[AnonRateThrottle()]
    )
    def validate_token(self, request: HttpRequest, token: str):
        """Validate an invitation token (public endpoint – no auth required)."""
        invitation = invitation_backend.validate_token(token)

        if invitation is None:
            return ValidateTokenSchema(valid=False)

        return ValidateTokenSchema(
            valid=True,
            email=invitation.email,
            tenant_name=getattr(invitation.tenant, "name", ""),
            role=invitation.role,
            message=invitation.message,
        )

    # ── Resend invitation ──────────────────────────────────────────

    @http_post("/resend", response=ResponseSchema, throttle=[InvitationThrottle()])
    @load_user
    def resend_invitation(self, request: HttpRequest, payload: ResendInvitationSchema):
        """Resend a pending invitation (renews the token)."""
        from django.conf import settings

        Invitation = get_invitation_model()
        invitation = Invitation.objects.filter(
            token=payload.token, status=InvitationStatus.PENDING
        ).first()

        if invitation is None:
            return ResponseSchema(
                code=ExceptionCode.FAILED_ERROR,
                detail=_("No pending invitation found with this token."),
            )

        # Limit resends
        max_resends = getattr(settings, "INVITATION_MAX_RESENDS", 3)
        resend_count = getattr(invitation, "resend_count", 0)
        if resend_count >= max_resends:
            return ResponseSchema(
                code=ExceptionCode.FAILED_ERROR,
                detail=_("Maximum resend limit reached for this invitation."),
            )

        # Renew token
        invitation.token = invitation_backend.token_generator.make_token(invitation)
        invitation.resend_count = resend_count + 1
        invitation.save(update_fields=["token", "resend_count"])

        invitation_resent.send_robust(sender=self.__class__, invitation=invitation)

        return ResponseSchema(
            code=ExceptionCode.SUCCESS,
            detail=_("Invitation resent successfully."),
        )

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def respond_error(detail: str) -> InvitationResponseSchema:
        return InvitationResponseSchema(success=False, message=detail)

    @staticmethod
    def _check_invite_permission(user, tenant, requested_role: str) -> str | None:
        """
        Verify that the inviter has permission to assign the requested role.

        Rules:
            - Owner can invite any role
            - Admin can invite member or admin (not owner)
            - Member can only invite member

        Returns an error message string if forbidden, None if allowed.
        """
        from oxutils.auth.invitations.models import InvitationRole

        membership = tenant.users.filter(user=user).first()
        if membership is None:
            return str(_("You are not a member of this tenant."))

        role_hierarchy = {
            InvitationRole.OWNER: 3,
            InvitationRole.ADMIN: 2,
            InvitationRole.MEMBER: 1,
        }

        inviter_level = role_hierarchy.get(
            InvitationRole.OWNER
            if membership.is_owner
            else (InvitationRole.ADMIN if membership.is_admin else InvitationRole.MEMBER),
            0,
        )
        requested_level = role_hierarchy.get(requested_role, 0)

        if requested_level > inviter_level:
            return str(_("You cannot assign a role higher than your own."))

        return None
