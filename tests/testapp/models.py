"""
Test models for oxutils tests.
"""
from oxutils.oxiliere.models import BaseTenant, BaseTenantUser


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
