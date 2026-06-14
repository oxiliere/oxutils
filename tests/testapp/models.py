"""
Test models for oxutils tests.
"""
from django.conf import settings
from django.db import models

from oxutils.oxiliere.models import BaseTenant, BaseTenantUser
from oxutils.auth.invitations.models import BaseInvitation


class Tenant(BaseTenant):
    """Test Tenant model."""

    class Meta(BaseTenant.Meta):
        abstract = False
        app_label = 'testapp'


class TenantUser(BaseTenantUser):
    """Test TenantUser model."""

    class Meta(BaseTenantUser.Meta):
        abstract = False
        app_label = 'testapp'


class Invitation(BaseInvitation):
    """Concrete Invitation for tests."""

    tenant = models.ForeignKey(
        settings.TENANT_MODEL,
        on_delete=models.CASCADE,
        related_name="invitations",
        verbose_name="tenant",
    )

    class Meta(BaseInvitation.Meta):
        abstract = False
        app_label = 'testapp'
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["email", "status"]),
        ]
