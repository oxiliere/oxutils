"""
Tests for Oxiliere permissions.
"""

from unittest.mock import Mock

from django.contrib.auth.models import AnonymousUser

from oxutils.oxiliere.permissions import (
    IsTenantAdmin,
    IsTenantOwner,
    IsTenantUser,
    TenantAdminPermission,
    TenantBasePermission,
    TenantOwnerPermission,
    TenantUserPermission,
)


def _mock_tenant_user(status="active", is_owner=False, is_admin=False):
    """Build a mock TenantUser row (the DB model, attached as tenant.user)."""
    tu = Mock()
    tu.status = status
    tu.is_owner = is_owner
    tu.is_admin = is_admin
    return tu


def _mock_tenant(tenant_user=None):
    """Build a mock DB tenant with an optional .user attribute."""
    tenant = Mock()
    tenant.oxi_id = "test-org"
    tenant.schema_name = "test_schema"
    if tenant_user is not None:
        tenant.user = tenant_user
    return tenant


class TestTenantBasePermission:
    """Test TenantBasePermission abstract base class."""

    def test_unauthenticated_user_denied(self):
        """Test permission denied for unauthenticated user."""

        class TestPermission(TenantBasePermission):
            def check_tenant_permission(self, request):
                return True

        permission = TestPermission()
        mock_request = Mock()
        mock_request.user = AnonymousUser()

        result = permission.has_permission(mock_request)

        assert result is False

    def test_no_user_denied(self):
        """Test permission denied when no user in request."""

        class TestPermission(TenantBasePermission):
            def check_tenant_permission(self, request):
                return True

        permission = TestPermission()
        mock_request = Mock()
        mock_request.user = None

        result = permission.has_permission(mock_request)

        assert result is False

    def test_no_tenant_denied(self):
        """Test permission denied when no tenant in request."""

        class TestPermission(TenantBasePermission):
            def check_tenant_permission(self, request):
                return True

        permission = TestPermission()
        mock_user = Mock()
        mock_user.is_authenticated = True

        mock_request = Mock(spec=["user"])
        mock_request.user = mock_user

        result = permission.has_permission(mock_request)

        assert result is False

    def test_tenant_without_user_denied(self):
        """Test permission denied when tenant has no .user attached."""

        class TestPermission(TenantBasePermission):
            def check_tenant_permission(self, request):
                return True

        permission = TestPermission()
        mock_user = Mock()
        mock_user.is_authenticated = True

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = Mock(spec=[])  # no .user attribute

        result = permission.has_permission(mock_request)

        assert result is False


class TestTenantUserPermission:
    """Test TenantUserPermission / IsTenantUser."""

    def test_permission_granted_for_active_tenant_user(self):
        """Test permission granted for active tenant user."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(_mock_tenant_user(status="active"))

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        permission = TenantUserPermission()
        result = permission.has_permission(mock_request)

        assert result is True

    def test_permission_denied_for_inactive_tenant_user(self):
        """Test permission denied for inactive tenant user."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(_mock_tenant_user(status="inactive"))

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        permission = TenantUserPermission()
        result = permission.has_permission(mock_request)

        assert result is False

    def test_permission_denied_for_no_tenant_user(self):
        """Test permission denied when tenant has no user."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(None)  # No tenant user

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        permission = TenantUserPermission()
        result = permission.has_permission(mock_request)

        assert result is False

    def test_singleton_instance_works(self):
        """Test IsTenantUser singleton instance."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(_mock_tenant_user(status="active"))

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        result = IsTenantUser.has_permission(mock_request)

        assert result is True


class TestTenantAdminPermission:
    """Test TenantAdminPermission / IsTenantAdmin."""

    def test_permission_granted_for_admin(self):
        """Test permission granted for admin."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(_mock_tenant_user(status="active", is_admin=True))

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        permission = TenantAdminPermission()
        result = permission.has_permission(mock_request)

        assert result is True

    def test_permission_denied_for_non_admin(self):
        """Test permission denied for regular user."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(_mock_tenant_user(status="active", is_admin=False))

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        permission = TenantAdminPermission()
        result = permission.has_permission(mock_request)

        assert result is False

    def test_singleton_instance_works(self):
        """Test IsTenantAdmin singleton instance."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(_mock_tenant_user(status="active", is_admin=True))

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        result = IsTenantAdmin.has_permission(mock_request)

        assert result is True


class TestTenantOwnerPermission:
    """Test TenantOwnerPermission / IsTenantOwner."""

    def test_permission_granted_for_owner(self):
        """Test permission granted for owner."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(_mock_tenant_user(status="active", is_owner=True))

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        permission = TenantOwnerPermission()
        result = permission.has_permission(mock_request)

        assert result is True

    def test_permission_denied_for_admin_non_owner(self):
        """Test permission denied for admin who is not owner."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(_mock_tenant_user(status="active", is_owner=False, is_admin=True))

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        permission = TenantOwnerPermission()
        result = permission.has_permission(mock_request)

        assert result is False

    def test_singleton_instance_works(self):
        """Test IsTenantOwner singleton instance."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(_mock_tenant_user(status="active", is_owner=True))

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        result = IsTenantOwner.has_permission(mock_request)

        assert result is True


class TestPermissionIntegration:
    """Test permission integration scenarios."""

    def test_owner_has_all_permissions(self):
        """Test owner passes all permission checks."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(_mock_tenant_user(status="active", is_owner=True, is_admin=True))

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        assert IsTenantUser.has_permission(mock_request) is True
        assert IsTenantOwner.has_permission(mock_request) is True
        assert IsTenantAdmin.has_permission(mock_request) is True

    def test_admin_has_user_and_admin_permissions(self):
        """Test admin passes user and admin checks but not owner."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(_mock_tenant_user(status="active", is_owner=False, is_admin=True))

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        assert IsTenantUser.has_permission(mock_request) is True
        assert IsTenantOwner.has_permission(mock_request) is False
        assert IsTenantAdmin.has_permission(mock_request) is True

    def test_regular_user_has_only_user_permission(self):
        """Test regular user only passes basic user check."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(_mock_tenant_user(status="active", is_owner=False, is_admin=False))

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        assert IsTenantUser.has_permission(mock_request) is True
        assert IsTenantOwner.has_permission(mock_request) is False
        assert IsTenantAdmin.has_permission(mock_request) is False

    def test_inactive_user_has_no_permissions(self):
        """Test inactive user fails all permission checks."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(_mock_tenant_user(status="inactive", is_owner=True, is_admin=True))

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        assert IsTenantUser.has_permission(mock_request) is False
        assert IsTenantOwner.has_permission(mock_request) is False
        assert IsTenantAdmin.has_permission(mock_request) is False

    def test_kwargs_passed_to_permission(self):
        """Test that kwargs are properly handled by permissions."""
        mock_user = Mock()
        mock_user.is_authenticated = True

        tenant = _mock_tenant(_mock_tenant_user(status="active"))

        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant

        # Should work with kwargs
        result = IsTenantUser.has_permission(mock_request, view=Mock(), extra_param="test")

        assert result is True
