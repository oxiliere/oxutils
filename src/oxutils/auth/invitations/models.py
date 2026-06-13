"""
Invitation model for tenant-based user invitations.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from oxutils.models import BaseModelMixin


class InvitationStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    ACCEPTED = "accepted", _("Accepted")
    EXPIRED = "expired", _("Expired")
    CANCELLED = "cancelled", _("Cancelled")


class InvitationRole(models.TextChoices):
    MEMBER = "member", _("Member")
    ADMIN = "admin", _("Admin")
    OWNER = "owner", _("Owner")


class Invitation(BaseModelMixin):
    """
    Invitation model that links a Tenant, an inviter (User), and an invitee (User or email).
    """

    tenant = models.ForeignKey(
        settings.TENANT_MODEL,
        on_delete=models.CASCADE,
        related_name="invitations",
        verbose_name=_("tenant"),
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_invitations",
        verbose_name=_("invited by"),
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="received_invitations",
        verbose_name=_("invitee"),
    )
    email = models.EmailField(_("email address"))
    token = models.CharField(_("token"), max_length=128, unique=True, db_index=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=InvitationRole.choices,
        default=InvitationRole.MEMBER,
    )
    expires_at = models.DateTimeField(_("expires at"), null=True, blank=True)
    accepted_at = models.DateTimeField(_("accepted at"), null=True, blank=True)
    resend_count = models.PositiveSmallIntegerField(_("resend count"), default=0)
    message = models.TextField(_("message"), blank=True, default="")

    class Meta:
        verbose_name = _("invitation")
        verbose_name_plural = _("invitations")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["email", "status"]),
        ]

    def __str__(self):
        return f"{self.email} → {self.tenant} ({self.status})"

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    @property
    def is_pending(self) -> bool:
        return self.status == InvitationStatus.PENDING and not self.is_expired

    def accept(self, user) -> None:
        """Accept the invitation: add user to tenant and mark as accepted."""
        from oxutils.oxiliere.models import BaseTenant

        self.status = InvitationStatus.ACCEPTED
        self.accepted_at = timezone.now()
        self.invitee = user
        self.save(update_fields=["status", "accepted_at", "invitee"])

        # Add user to tenant
        is_owner = self.role == InvitationRole.OWNER
        is_admin = self.role in (InvitationRole.ADMIN, InvitationRole.OWNER)
        self.tenant.add_user(user, is_owner=is_owner, is_admin=is_admin)

    def cancel(self) -> None:
        """Cancel this invitation."""
        self.status = InvitationStatus.CANCELLED
        self.save(update_fields=["status"])

    def mark_expired(self) -> None:
        """Mark this invitation as expired."""
        self.status = InvitationStatus.EXPIRED
        self.save(update_fields=["status"])
