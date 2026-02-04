"""
Tests for Oxiliere permissions.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth.models import AnonymousUser
from oxutils.oxiliere.permissions import (
    TenantBasePermission,
    TenantUserPermission,
    TenantOwnerPermission,
    TenantAdminPermission,
    OxiliereServicePermission,
    IsTenantUser,
    IsTenantOwner,
    IsTenantAdmin,
    IsOxiliereService,
)
from oxutils.jwt.models import TokenTenant, TenantUser
from oxutils.jwt.tokens import OxilierServiceToken
from oxutils.constants import OXILIERE_SERVICE_TOKEN


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
        
        mock_request = Mock(spec=['user'])
        mock_request.user = mock_user
        
        result = permission.has_permission(mock_request)
        
        assert result is False
    
    def test_tenant_not_token_tenant_denied(self):
        """Test permission denied when tenant is not a TokenTenant."""
        class TestPermission(TenantBasePermission):
            def check_tenant_permission(self, request):
                return True
        
        permission = TestPermission()
        mock_user = Mock()
        mock_user.is_authenticated = True
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = Mock()  # Not a TokenTenant
        
        result = permission.has_permission(mock_request)
        
        assert result is False


class TestTenantUserPermission:
    """Test TenantUserPermission / IsTenantUser."""
    
    def _create_tenant(self, tenant_user=None):
        """Helper to create TokenTenant."""
        return TokenTenant(
            schema_name='test_schema',
            tenant_id='100',
            oxi_id='test-org',
            subscription_plan='basic',
            subscription_status='active',
            subscription_end_date='2025-12-31',
            status='active',
            user=tenant_user
        )
    
    def test_permission_granted_for_active_tenant_user(self):
        """Test permission granted for active tenant user."""
        mock_user = Mock()
        mock_user.is_authenticated = True
        
        tenant_user = TenantUser(
            oxi_id='user-123',
            id='1',
            is_owner=False,
            is_admin=False,
            status='active'
        )
        tenant = self._create_tenant(tenant_user)
        
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
        
        tenant_user = TenantUser(
            oxi_id='user-123',
            id='1',
            is_owner=False,
            is_admin=False,
            status='inactive'
        )
        tenant = self._create_tenant(tenant_user)
        
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
        
        tenant = self._create_tenant(None)  # No tenant user
        
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
        
        tenant_user = TenantUser(
            oxi_id='user-123',
            id='1',
            is_owner=False,
            is_admin=False,
            status='active'
        )
        tenant = self._create_tenant(tenant_user)
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant
        
        result = IsTenantUser.has_permission(mock_request)
        
        assert result is True


class TestTenantAdminPermission:
    """Test TenantAdminPermission / IsTenantAdmin."""
    
    def _create_tenant(self, tenant_user=None):
        """Helper to create TokenTenant."""
        return TokenTenant(
            schema_name='test_schema',
            tenant_id='100',
            oxi_id='test-org',
            subscription_plan='basic',
            subscription_status='active',
            subscription_end_date='2025-12-31',
            status='active',
            user=tenant_user
        )
    
    def test_permission_granted_for_admin(self):
        """Test permission granted for admin."""
        mock_user = Mock()
        mock_user.is_authenticated = True
        
        tenant_user = TenantUser(
            oxi_id='user-123',
            id='1',
            is_owner=False,
            is_admin=True,
            status='active'
        )
        tenant = self._create_tenant(tenant_user)
        
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
        
        tenant_user = TenantUser(
            oxi_id='user-123',
            id='1',
            is_owner=False,
            is_admin=False,
            status='active'
        )
        tenant = self._create_tenant(tenant_user)
        
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
        
        tenant_user = TenantUser(
            oxi_id='user-123',
            id='1',
            is_owner=False,
            is_admin=True,
            status='active'
        )
        tenant = self._create_tenant(tenant_user)
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant
        
        result = IsTenantAdmin.has_permission(mock_request)
        
        assert result is True


class TestTenantOwnerPermission:
    """Test TenantOwnerPermission / IsTenantOwner."""
    
    def _create_tenant(self, tenant_user=None):
        """Helper to create TokenTenant."""
        return TokenTenant(
            schema_name='test_schema',
            tenant_id='100',
            oxi_id='test-org',
            subscription_plan='basic',
            subscription_status='active',
            subscription_end_date='2025-12-31',
            status='active',
            user=tenant_user
        )
    
    def test_permission_granted_for_owner(self):
        """Test permission granted for owner."""
        mock_user = Mock()
        mock_user.is_authenticated = True
        
        tenant_user = TenantUser(
            oxi_id='user-123',
            id='1',
            is_owner=True,
            is_admin=False,
            status='active'
        )
        tenant = self._create_tenant(tenant_user)
        
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
        
        tenant_user = TenantUser(
            oxi_id='user-123',
            id='1',
            is_owner=False,
            is_admin=True,
            status='active'
        )
        tenant = self._create_tenant(tenant_user)
        
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
        
        tenant_user = TenantUser(
            oxi_id='user-123',
            id='1',
            is_owner=True,
            is_admin=False,
            status='active'
        )
        tenant = self._create_tenant(tenant_user)
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant
        
        result = IsTenantOwner.has_permission(mock_request)
        
        assert result is True


class TestOxiliereServicePermission:
    """Test OxiliereServicePermission class."""
    
    def test_permission_valid_service_token_from_header(self):
        """Test permission granted with valid service token from header."""
        permission = OxiliereServicePermission()
        
        # Create valid service token
        token = OxilierServiceToken.for_service({'service': 'test'})
        token_str = str(token)
        
        mock_request = Mock()
        mock_request.headers.get.return_value = token_str
        mock_request.META.get.return_value = None
        
        result = permission.has_permission(mock_request)
        
        assert result is True
        mock_request.headers.get.assert_called_once_with(OXILIERE_SERVICE_TOKEN)
    
    def test_permission_valid_service_token_from_meta(self):
        """Test permission granted with valid service token from META."""
        permission = OxiliereServicePermission()
        
        # Create valid service token
        token = OxilierServiceToken.for_service({'service': 'test'})
        token_str = str(token)
        
        mock_request = Mock()
        mock_request.headers.get.return_value = None
        mock_request.META.get.return_value = token_str
        
        result = permission.has_permission(mock_request)
        
        assert result is True
    
    def test_permission_invalid_service_token(self):
        """Test permission denied with invalid service token."""
        permission = OxiliereServicePermission()
        
        mock_request = Mock()
        mock_request.headers.get.return_value = "invalid.token.string"
        mock_request.META.get.return_value = None
        
        result = permission.has_permission(mock_request)
        
        assert result is False
    
    def test_permission_no_service_token(self):
        """Test permission denied when no service token provided."""
        permission = OxiliereServicePermission()
        
        mock_request = Mock()
        mock_request.headers.get.return_value = None
        mock_request.META.get.return_value = None
        
        result = permission.has_permission(mock_request)
        
        assert result is False
    
    def test_permission_expired_service_token(self):
        """Test permission denied with expired service token."""
        permission = OxiliereServicePermission()
        
        # Create expired token
        from datetime import datetime, timedelta
        token = OxilierServiceToken.for_service({'service': 'test'})
        token.payload['exp'] = datetime.now() - timedelta(hours=1)
        token_str = str(token)
        
        mock_request = Mock()
        mock_request.headers.get.return_value = token_str
        mock_request.META.get.return_value = None
        
        result = permission.has_permission(mock_request)
        
        assert result is False
    
    def test_permission_header_name_conversion(self):
        """Test correct header name conversion for META."""
        permission = OxiliereServicePermission()
        
        token = OxilierServiceToken.for_service({'service': 'test'})
        token_str = str(token)
        
        mock_request = Mock()
        mock_request.headers.get.return_value = None
        
        # Mock META to capture the key used
        meta_dict = {}
        mock_request.META.get = lambda key: meta_dict.get(key)
        
        # Set token in META with converted key
        expected_meta_key = 'HTTP_' + OXILIERE_SERVICE_TOKEN.upper().replace('-', '_')
        meta_dict[expected_meta_key] = token_str
        
        result = permission.has_permission(mock_request)
        
        assert result is True
    
    def test_singleton_instance_works(self):
        """Test IsOxiliereService singleton instance."""
        token = OxilierServiceToken.for_service({'service': 'test'})
        
        mock_request = Mock()
        mock_request.headers.get.return_value = str(token)
        mock_request.META.get.return_value = None
        
        result = IsOxiliereService.has_permission(mock_request)
        
        assert result is True


class TestPermissionIntegration:
    """Test permission integration scenarios."""
    
    def _create_tenant(self, is_owner=False, is_admin=False, status='active'):
        """Helper to create TokenTenant with user."""
        tenant_user = TenantUser(
            oxi_id='user-123',
            id='1',
            is_owner=is_owner,
            is_admin=is_admin,
            status=status
        )
        return TokenTenant(
            schema_name='test_schema',
            tenant_id='100',
            oxi_id='test-org',
            subscription_plan='basic',
            subscription_status='active',
            subscription_end_date='2025-12-31',
            status='active',
            user=tenant_user
        )
    
    def test_owner_has_all_permissions(self):
        """Test owner passes all permission checks."""
        mock_user = Mock()
        mock_user.is_authenticated = True
        
        tenant = self._create_tenant(is_owner=True, is_admin=True)
        
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
        
        tenant = self._create_tenant(is_owner=False, is_admin=True)
        
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
        
        tenant = self._create_tenant(is_owner=False, is_admin=False)
        
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
        
        tenant = self._create_tenant(is_owner=True, is_admin=True, status='inactive')
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant
        
        assert IsTenantUser.has_permission(mock_request) is False
        assert IsTenantOwner.has_permission(mock_request) is False
        assert IsTenantAdmin.has_permission(mock_request) is False
    
    def test_service_permission_independent_of_user(self):
        """Test service permission works independently of user permission."""
        token = OxilierServiceToken.for_service({'service': 'api'})
        
        mock_request = Mock()
        mock_request.headers.get.return_value = str(token)
        mock_request.META.get.return_value = None
        mock_request.user = AnonymousUser()  # No user
        
        # Service permission should pass even without user
        assert IsOxiliereService.has_permission(mock_request) is True
        
        # But tenant permission should fail
        assert IsTenantUser.has_permission(mock_request) is False
    
    def test_kwargs_passed_to_permission(self):
        """Test that kwargs are properly handled by permissions."""
        mock_user = Mock()
        mock_user.is_authenticated = True
        
        tenant_user = TenantUser(
            oxi_id='user-123',
            id='1',
            is_owner=False,
            is_admin=False,
            status='active'
        )
        tenant = TokenTenant(
            schema_name='test_schema',
            tenant_id='100',
            oxi_id='test-org',
            subscription_plan='basic',
            subscription_status='active',
            subscription_end_date='2025-12-31',
            status='active',
            user=tenant_user
        )
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = tenant
        
        # Should work with kwargs
        result = IsTenantUser.has_permission(mock_request, view=Mock(), extra_param='test')
        
        assert result is True
