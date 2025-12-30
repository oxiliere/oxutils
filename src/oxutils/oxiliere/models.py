import time
import uuid
import structlog
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django_tenants.models import TenantMixin
from oxutils.models import (
    BaseModelMixin,
)
from oxutils.oxiliere.enums import TenantStatus
from oxutils.oxiliere.exceptions import DeleteError
from oxutils.oxiliere.signals import (
    tenant_user_removed,
    tenant_user_added,
)
from oxutils.oxiliere.utils import (
    is_system_tenant,
    generate_schema_name,
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


class BaseTenant(TenantMixin, BaseModelMixin):
    name = models.CharField(max_length=100)
    oxi_id = models.CharField(unique=True, max_length=25)
    subscription_plan = models.CharField(max_length=255, null=True, blank=True)
    subscription_status = models.CharField(max_length=255, null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=TenantStatus.choices,
        default=TenantStatus.ACTIVE
    )

    # soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    suffix = models.CharField(max_length=8, editable=False)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True
    # Schema will be automatically deleted when related tenant is deleted
    auto_drop_schema = True

    objects = models.Manager()
    active = TenantManager()


    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.suffix = uuid.uuid4().hex[:8]
            self.schema_name = generate_schema_name(self.oxi_id, self.suffix)
        super().save(*args, **kwargs)

    def delete(self, *args, force_drop: bool = False, **kwargs) -> None:
        """Override deleting of Tenant object.

        Args:
            force_drop (bool): If True, forces the deletion of the object. Defaults to False.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        if force_drop:
            super().delete(force_drop, *args, **kwargs)
        else:
            logger.warning("Tenant deletion is not allowed. Use delete_tenant to delete the tenant.")
            raise DeleteError(_("Tenant deletion is not allowed. Use delete_tenant to delete the tenant."))

    def delete_tenant(self) -> None:
        """Mark tenant for deletion."""

        if self.is_deleted:
            return

        # Prevent public tenant schema from being deleted
        if is_system_tenant(self):
            logger.warning("Cannot delete public tenant schema.")
            raise ValueError(_("Cannot delete public tenant schema"))

        time_string = str(int(time.time()))
        new_id = f"{time_string}-deleted-{self.oxi_id}"

        self.oxi_id = new_id
        self.deleted_at = timezone.now()
        self.is_deleted = True
        self.is_active = False
        self.status = TenantStatus.DELETED

        self.save(update_fields=[
            'oxi_id', 'deleted_at', 'is_deleted', 'is_active', 'status'
        ])

    def restore(self):
        if not self.is_deleted:
            return

        oxi_id = self.oxi_id.split("-deleted-")[1]
        self.oxi_id = oxi_id
        self.is_deleted = False
        self.deleted_at = None
        self.is_active = True
        self.status = TenantStatus.ACTIVE
        self.save(update_fields=["oxi_id", "is_deleted", "deleted_at", "is_active", "status"])

    
    def add_user(self, user: AbstractBaseUser, is_owner: bool = False, is_admin: bool = False):
        """Add user to tenant."""

        if self.users.filter(user=user).exists():
            logger.warning("User is already a member of this tenant.")
            raise ValueError(_("User is already a member of this tenant."))

        self.users.create(user=user, is_owner=is_owner, is_admin=is_admin)
        tenant_user_added.send(sender=self.__class__, tenant=self, user=user)
        

    def remove_user(self, user: AbstractBaseUser):
        """Remove user from tenant."""

        if not self.users.filter(user=user).exists():
            logger.warning("User is not a member of this tenant.")
            raise ValueError("User is not a member of this tenant.")

        self.users.filter(user=user).delete()
        logger.info("User removed from tenant.")
        tenant_user_removed.send(sender=self.__class__, tenant=self, user=user)
        

    class Meta:
        abstract = True
        verbose_name = _('Tenant')
        verbose_name_plural = _('Tenants')
        indexes = [
            models.Index(fields=['schema_name']),
            models.Index(fields=['oxi_id']),
            models.Index(fields=['is_deleted']),
            models.Index(fields=['oxi_id', 'is_deleted'])
        ]


class BaseTenantUser(BaseModelMixin):
    tenant = models.ForeignKey(
        settings.TENANT_MODEL, 
        on_delete=models.CASCADE,
        related_name='users'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='tenants'
    )
    is_owner = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=TenantStatus.choices,
        default=TenantStatus.ACTIVE
    )

    class Meta:
        abstract = True
        verbose_name = 'Tenant User'
        verbose_name_plural = 'Tenant Users'
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'user'],
                name='unique_tenant_user'
            )
        ]
        indexes = [
            models.Index(fields=['tenant', 'user'])
        ]
