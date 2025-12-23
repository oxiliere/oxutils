from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django_tenants.models import TenantMixin
from oxutils.models import (
    TimestampMixin,
    BaseModelMixin,
    UUIDPrimaryKeyMixin,
)
from oxutils.oxiliere.enums import TenantStatus




tenant_model = getattr(settings, 'TENANT_MODEL', 'oxiliere.Tenant')
tenant_user_model = getattr(settings, 'TENANT_USER_MODEL', 'oxiliere.TenantUser')



class BaseTenant(TenantMixin, UUIDPrimaryKeyMixin, TimestampMixin):
    name = models.CharField(max_length=100)
    oxi_id = models.CharField(unique=True)
    subscription_plan = models.CharField(max_length=255, null=True, blank=True)
    subscription_status = models.CharField(max_length=255, null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=TenantStatus.choices,
        default=TenantStatus.ACTIVE
    )

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True

    class Meta:
        abstract = True
        verbose_name = _('Tenant')
        verbose_name_plural = _('Tenants')
        indexes = [
            models.Index(fields=['oxi_id'])
        ]


class BaseTenantUser(BaseModelMixin):
    tenant = models.ForeignKey(
        tenant_model, on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
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


class Tenant(BaseTenant):
    class Meta(BaseTenant.Meta):
        abstract = not tenant_model == 'oxiliere.Tenant'


class TenantUser(BaseTenantUser):
    class Meta(BaseTenantUser.Meta):
        abstract = not tenant_user_model == 'oxiliere.TenantUser'
