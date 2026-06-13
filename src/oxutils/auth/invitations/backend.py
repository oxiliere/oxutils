"""
Invitation backend – service layer for invitation lifecycle management.
"""
import structlog
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from oxutils.auth.invitations.models import Invitation, InvitationStatus, InvitationRole
from oxutils.auth.invitations.tokens import InvitationTokenGenerator

logger = structlog.get_logger(__name__)


class InvitationBackend:
    """
    Manages the full lifecycle of tenant invitations.

    Responsibilities:
        - Create / send invitations
        - Accept invitations (add user to tenant)
        - Cancel / expire invitations
        - List invitations for users or tenants
    """

    def __init__(self):
        self.token_generator = InvitationTokenGenerator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_invitation(
        self,
        *,
        tenant,
        email: str,
        invited_by,
        role: str = InvitationRole.MEMBER,
        message: str = "",
    ) -> Invitation:
        """
        Create a new invitation for an email address.

        Raises ValueError if:
            - The email is already a member of the tenant
            - A pending invitation already exists for this email + tenant
        """
        email = email.lower().strip()

        # Check user not already in tenant
        self._ensure_not_already_member(tenant, email)

        # Check no duplicate pending invitation
        self._ensure_no_duplicate(tenant, email)

        # Check max invitations limit
        self._check_rate_limit(invited_by)

        with transaction.atomic():
            invitation = Invitation.objects.create(
                tenant=tenant,
                invited_by=invited_by,
                email=email,
                role=role,
                status=InvitationStatus.PENDING,
                expires_at=self._default_expiry(),
                message=message,
            )
            # Generate token after creation (needs pk)
            invitation.token = self.token_generator.make_token(invitation)
            invitation.save(update_fields=["token"])

        logger.info(
            "invitation_created",
            invitation_id=str(invitation.pk),
            tenant=tenant.oxi_id,
            email=email,
            role=role,
        )
        return invitation

    def accept_invitation(self, token: str, user) -> Invitation:
        """
        Accept an invitation with a token. The user is added to the tenant.

        Raises ValueError if:
            - Invitation not found or token invalid
            - Invitation already accepted/expired/cancelled
        """
        invitation = self._get_valid_invitation(token)

        with transaction.atomic():
            invitation.accept(user)

        logger.info(
            "invitation_accepted",
            invitation_id=str(invitation.pk),
            user_id=str(user.pk),
            tenant=invitation.tenant.oxi_id,
        )
        return invitation

    def cancel_invitation(self, token: str, cancelled_by) -> Invitation:
        """Cancel a pending invitation."""
        invitation = self._get_pending_invitation(token)
        invitation.cancel()
        logger.info(
            "invitation_cancelled",
            invitation_id=str(invitation.pk),
            cancelled_by=str(cancelled_by.pk),
        )
        return invitation

    def validate_token(self, token: str) -> Optional[Invitation]:
        """Validate a token and return the invitation if valid, else None."""
        try:
            return self._get_valid_invitation(token)
        except ValueError:
            return None

    def get_user_invitations(self, user) -> QuerySet:
        """Return all pending invitations for a user's email addresses."""
        from allauth.account.models import EmailAddress

        emails = list(
            EmailAddress.objects.filter(user=user).values_list("email", flat=True)
        )
        if user.email:
            emails.append(user.email)

        return Invitation.objects.filter(
            email__in=emails,
            status=InvitationStatus.PENDING,
            expires_at__gt=timezone.now(),
        ).select_related("tenant", "invited_by")

    def get_tenant_invitations(self, tenant) -> QuerySet:
        """Return all invitations for a tenant."""
        return Invitation.objects.filter(tenant=tenant).select_related("invited_by", "invitee")

    def expire_stale_invitations(self) -> int:
        """Mark all expired pending invitations as EXPIRED. Returns count."""
        count = Invitation.objects.filter(
            status=InvitationStatus.PENDING,
            expires_at__lt=timezone.now(),
        ).update(status=InvitationStatus.EXPIRED)
        if count:
            logger.info("invitations_expired", count=count)
        return count

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_valid_invitation(self, token: str) -> Invitation:
        """Fetch a pending invitation by token and validate it."""
        invitation = Invitation.objects.filter(token=token).select_related("tenant").first()

        if invitation is None:
            raise ValueError(_("Invitation not found."))

        if invitation.status == InvitationStatus.ACCEPTED:
            raise ValueError(_("This invitation has already been accepted."))
        if invitation.status == InvitationStatus.CANCELLED:
            raise ValueError(_("This invitation has been cancelled."))
        if invitation.is_expired:
            invitation.mark_expired()
            raise ValueError(_("This invitation has expired."))

        return invitation

    def _get_pending_invitation(self, token: str) -> Invitation:
        invitation = Invitation.objects.filter(
            token=token, status=InvitationStatus.PENDING
        ).first()
        if invitation is None:
            raise ValueError(_("No pending invitation found with this token."))
        return invitation

    def _ensure_not_already_member(self, tenant, email: str) -> None:
        """Check that the email is not already a member of the tenant."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.filter(email=email).first()
        if user and tenant.users.filter(user=user).exists():
            raise ValueError(_("This user is already a member of the tenant."))

    def _ensure_no_duplicate(self, tenant, email: str) -> None:
        if Invitation.objects.filter(
            tenant=tenant,
            email=email,
            status=InvitationStatus.PENDING,
            expires_at__gt=timezone.now(),
        ).exists():
            raise ValueError(_("A pending invitation already exists for this email."))

    def _check_rate_limit(self, invited_by) -> None:
        max_invites = getattr(settings, "INVITATIONS_MAX_PER_HOUR", 50)
        one_hour_ago = timezone.now() - timedelta(hours=1)
        count = Invitation.objects.filter(
            invited_by=invited_by, created_at__gte=one_hour_ago
        ).count()
        if count >= max_invites:
            raise ValueError(_("You have reached the invitation limit. Please try again later."))

    def _default_expiry(self):
        days = getattr(settings, "INVITATION_EXPIRY_DAYS", 7)
        return timezone.now() + timedelta(days=days)


# Singleton
invitation_backend = InvitationBackend()
