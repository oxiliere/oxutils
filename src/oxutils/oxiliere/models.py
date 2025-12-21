from django.db import models
from django.conf import settings
from django_tenants.models import TenantMixin, DomainMixin
from oxutils.models import (
    TimestampMixin,
    BaseModelMixin,
)
from oxutils.oxiliere.enums import TenantStatus




class Tenant(TenantMixin, TimestampMixin):
    name = models.CharField(max_length=100)
    oxi_id = models.UUIDField(unique=True)
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


class Domain(DomainMixin):
    pass



class TenantUser(BaseModelMixin):
    tenant = models.ForeignKey(
        settings.TENANT_MODEL, on_delete=models.CASCADE
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
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'user'],
                name='unique_tenant_user'
            )
        ]
