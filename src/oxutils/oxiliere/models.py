import time
import uuid

import structlog
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_tenants.models import TenantMixin

from oxutils.models import (
    BaseModelMixin,
    ChangeTrackerMixin,
)
from oxutils.oxiliere.enums import TenantStatus
from oxutils.oxiliere.exceptions import DeleteError
from oxutils.oxiliere.signals import (
    tenant_created,
    tenant_deleted,
    tenant_force_dropped,
    tenant_restored,
    tenant_subscription_changed,
    tenant_user_activated,
    tenant_user_added,
    tenant_user_deactivated,
    tenant_user_removed,
    tenant_user_role_changed,
)
from oxutils.oxiliere.utils import (
    generate_schema_name,
    is_system_tenant,
)

logger = structlog.get_logger(__name__)


class TenantQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)


class TenantManager(models.Manager):
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db).active()


class BaseTenant(TenantMixin, BaseModelMixin, ChangeTrackerMixin):
    name = models.CharField(max_length=100)
    oxi_id = models.CharField(unique=True, max_length=25)
    subscription_plan = models.CharField(max_length=255, null=True, blank=True)
    subscription_status = models.CharField(max_length=255, null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=TenantStatus.choices,
        default=TenantStatus.PENDING_MIGRATION,
        help_text=_("PENDING_MIGRATION: schema not yet created, ACTIVE: ready, "
                      "INACTIVE/SUSPENDED/DELETED/REMOVED: not accessible"),
    )

    # Fields tracked for change detection (subscription + status signals)
    TRACKED_FIELDS = ("subscription_plan", "subscription_status", "subscription_end_date", "status")

    # State machine — allowed transitions
    _ALLOWED_TRANSITIONS = {
        TenantStatus.PENDING_MIGRATION: {TenantStatus.ACTIVE, TenantStatus.INACTIVE, TenantStatus.DELETED},
        TenantStatus.ACTIVE: {TenantStatus.INACTIVE, TenantStatus.SUSPENDED, TenantStatus.DELETED},
        TenantStatus.INACTIVE: {TenantStatus.ACTIVE, TenantStatus.DELETED},
        TenantStatus.SUSPENDED: {TenantStatus.ACTIVE, TenantStatus.DELETED},
        TenantStatus.DELETED: {TenantStatus.PENDING_MIGRATION},  # restore
    }

    def _validate_transition(self) -> None:
        """Raise ValueError if the status is changing to an invalid next state."""
        if "status" not in (self.TRACKED_FIELDS or ()):
            return
        new_status = getattr(self, "status", None)
        old_status = self._snapshot.get("status")
        if old_status is None or new_status == old_status:
            return
        allowed = self._ALLOWED_TRANSITIONS.get(old_status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Invalid status transition: {old_status} → {new_status}. "
                f"Allowed: {allowed}"
            )

    def transition_to(self, new_status: str) -> None:
        """Public API to change status with validation."""
        self.status = new_status
        self._validate_transition()

    # soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    suffix = models.CharField(max_length=8, editable=False)

    # Schema operations are deferred to Celery tasks via signals.
    # Listen to tenant_created / tenant_deleted / tenant_restored
    # to trigger schema creation/drop/restore asynchronously.
    auto_create_schema = False
    auto_drop_schema = False

    objects = models.Manager()
    active = TenantManager()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if is_new:
            self.suffix = uuid.uuid4().hex[:8]
            self.schema_name = generate_schema_name(self.oxi_id, self.suffix)
        else:
            self._validate_transition()

        changed = self.pop_changes()
        subscription_changed = {
            k: v for k, v in changed.items()
            if k in ("subscription_plan", "subscription_status", "subscription_end_date")
        }

        super().save(*args, **kwargs)

        if is_new:
            tenant_created.send_robust(sender=self.__class__, tenant=self)
        elif subscription_changed:
            tenant_subscription_changed.send_robust(
                sender=self.__class__, tenant=self, previous=subscription_changed
            )

    def delete(self, *args, force_drop: bool = False, **kwargs) -> None:
        if force_drop:
            tenant_force_dropped.send_robust(sender=self.__class__, tenant=self)
            super().delete(force_drop, *args, **kwargs)
        else:
            logger.warning(
                "Tenant deletion is not allowed. Use delete_tenant to delete the tenant."
            )
            raise DeleteError(
                _("Tenant deletion is not allowed. Use delete_tenant to delete the tenant.")
            )

    def delete_tenant(self) -> None:
        """Mark tenant for deletion."""

        if self.is_deleted:
            return

        if is_system_tenant(self):
            logger.warning("Cannot delete public tenant schema.")
            raise ValueError(_("Cannot delete public tenant schema"))

        time_string = str(int(time.time()))
        new_id = f"{time_string}-deleted-{self.oxi_id}"

        self.oxi_id = new_id
        self.deleted_at = timezone.now()
        self.is_deleted = True
        self.is_active = False
        self.transition_to(TenantStatus.DELETED)

        self.save(update_fields=["oxi_id", "deleted_at", "is_deleted", "is_active", "status"])

        tenant_deleted.send_robust(sender=self.__class__, tenant=self)

    def restore(self):
        if not self.is_deleted:
            return

        oxi_id = self.oxi_id.split("-deleted-")[1]
        self.oxi_id = oxi_id
        self.is_deleted = False
        self.deleted_at = None
        self.is_active = True
        self.transition_to(TenantStatus.PENDING_MIGRATION)  # schema will be recreated async
        self.save(update_fields=["oxi_id", "is_deleted", "deleted_at", "is_active", "status"])

        tenant_restored.send_robust(sender=self.__class__, tenant=self)

    def add_user(self, user: AbstractBaseUser, is_owner: bool = False, is_admin: bool = False):
        """Add user to tenant."""

        if self.users.filter(user=user).exists():
            logger.warning("User is already a member of this tenant.")
            raise ValueError(_("User is already a member of this tenant."))

        self.users.create(user=user, is_owner=is_owner, is_admin=is_admin)
        tenant_user_added.send_robust(sender=self.__class__, tenant=self, user=user)

    def remove_user(self, user: AbstractBaseUser):
        """Remove user from tenant."""

        if not self.users.filter(user=user).exists():
            logger.warning("User is not a member of this tenant.")
            raise ValueError("User is not a member of this tenant.")

        self.users.filter(user=user).delete()
        logger.info("User removed from tenant.")
        tenant_user_removed.send_robust(sender=self.__class__, tenant=self, user=user)

    class Meta:
        abstract = True
        verbose_name = _("Tenant")
        verbose_name_plural = _("Tenants")
        indexes = [
            models.Index(fields=["schema_name"]),
            models.Index(fields=["oxi_id"]),
            models.Index(fields=["is_deleted"]),
            models.Index(fields=["oxi_id", "is_deleted"]),
        ]


class BaseTenantUser(BaseModelMixin, ChangeTrackerMixin):
    tenant = models.ForeignKey(
        settings.TENANT_MODEL, on_delete=models.CASCADE, related_name="users"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tenants"
    )
    is_owner = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=TenantStatus.choices, default=TenantStatus.ACTIVE
    )

    TRACKED_FIELDS = ("is_owner", "is_admin", "status")

    def save(self, *args, **kwargs):
        changed = self.pop_changes()
        old_status = changed.get("status")
        was_active = old_status == TenantStatus.ACTIVE if old_status else self.status == TenantStatus.ACTIVE

        super().save(*args, **kwargs)

        # Role changes (excluding status-only changes)
        role_keys = {"is_owner", "is_admin"}
        if role_keys & changed.keys() or ("status" in changed and old_status):
            tenant_user_role_changed.send_robust(
                sender=self.__class__, tenant_user=self, previous=changed
            )

        # Activation / deactivation
        if old_status is not None and self.status != old_status:
            if self.status == TenantStatus.ACTIVE:
                tenant_user_activated.send_robust(sender=self.__class__, tenant_user=self)
            elif was_active:
                tenant_user_deactivated.send_robust(sender=self.__class__, tenant_user=self)

        self.refresh_snapshot()

    class Meta:
        abstract = True
        verbose_name = "Tenant User"
        verbose_name_plural = "Tenant Users"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "user"], name="unique_tenant_user")
        ]
        indexes = [models.Index(fields=["tenant", "user"])]
