"""
Tests for Oxiliere permissions.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth.models import AnonymousUser
from oxutils.oxiliere.permissions import (
    TenantPermission,
    TenantOwnerPermission,
    TenantAdminPermission,
    TenantUserPermission,
    OxiliereServicePermission,
)
from oxutils.jwt.tokens import OxilierServiceToken
from oxutils.constants import OXILIERE_SERVICE_TOKEN


class TestTenantPermission:
    """Test TenantPermission class."""
    
    def test_permission_authenticated_user_with_access(self):
        """Test permission granted for authenticated user with tenant access."""
        permission = TenantPermission()
        
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.pk = 1
        
        mock_tenant = Mock()
        mock_tenant.pk = 100
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = mock_tenant
        
        with patch('oxutils.oxiliere.permissions.TenantUser') as mock_tenant_user:
            mock_tenant_user.objects.filter.return_value.exists.return_value = True
            
            result = permission.has_permission(mock_request)
            
            assert result is True
            mock_tenant_user.objects.filter.assert_called_once()
    
    def test_permission_authenticated_user_without_access(self):
        """Test permission denied for authenticated user without tenant access."""
        permission = TenantPermission()
        
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.pk = 1
        
        mock_tenant = Mock()
        mock_tenant.pk = 100
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = mock_tenant
        
        with patch('oxutils.oxiliere.permissions.TenantUser') as mock_tenant_user:
            mock_tenant_user.objects.filter.return_value.exists.return_value = False
            
            result = permission.has_permission(mock_request)
            
            assert result is False
    
    def test_permission_unauthenticated_user(self):
        """Test permission denied for unauthenticated user."""
        permission = TenantPermission()
        
        mock_request = Mock()
        mock_request.user = AnonymousUser()
        
        result = permission.has_permission(mock_request)
        
        assert result is False
    
    def test_permission_no_user(self):
        """Test permission denied when no user in request."""
        permission = TenantPermission()
        
        mock_request = Mock()
        mock_request.user = None
        
        result = permission.has_permission(mock_request)
        
        assert result is False
    
    def test_permission_no_tenant(self):
        """Test permission denied when no tenant in request."""
        permission = TenantPermission()
        
        mock_user = Mock()
        mock_user.is_authenticated = True
        
        mock_request = Mock(spec=['user'])
        mock_request.user = mock_user
        
        result = permission.has_permission(mock_request)
        
        assert result is False


class TestTenantOwnerPermission:
    """Test TenantOwnerPermission class."""
    
    def test_permission_owner_user(self):
        """Test permission granted for owner user."""
        permission = TenantOwnerPermission()
        
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.pk = 1
        
        mock_tenant = Mock()
        mock_tenant.pk = 100
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = mock_tenant
        
        with patch('oxutils.oxiliere.permissions.TenantUser') as mock_tenant_user:
            mock_tenant_user.objects.filter.return_value.exists.return_value = True
            
            result = permission.has_permission(mock_request)
            
            assert result is True
            # Verify is_owner=True was in filter
            call_kwargs = mock_tenant_user.objects.filter.call_args[1]
            assert call_kwargs['is_owner'] is True
    
    def test_permission_non_owner_user(self):
        """Test permission denied for non-owner user."""
        permission = TenantOwnerPermission()
        
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.pk = 1
        
        mock_tenant = Mock()
        mock_tenant.pk = 100
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = mock_tenant
        
        with patch('oxutils.oxiliere.permissions.TenantUser') as mock_tenant_user:
            mock_tenant_user.objects.filter.return_value.exists.return_value = False
            
            result = permission.has_permission(mock_request)
            
            assert result is False
    
    def test_permission_unauthenticated_user(self):
        """Test permission denied for unauthenticated user."""
        permission = TenantOwnerPermission()
        
        mock_request = Mock()
        mock_request.user = AnonymousUser()
        
        result = permission.has_permission(mock_request)
        
        assert result is False


class TestTenantAdminPermission:
    """Test TenantAdminPermission class."""
    
    def test_permission_admin_user(self):
        """Test permission granted for admin user."""
        permission = TenantAdminPermission()
        
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.pk = 1
        
        mock_tenant = Mock()
        mock_tenant.pk = 100
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = mock_tenant
        
        with patch('oxutils.oxiliere.permissions.TenantUser') as mock_tenant_user:
            mock_tenant_user.objects.filter.return_value.exists.return_value = True
            
            result = permission.has_permission(mock_request)
            
            assert result is True
            # Verify is_admin=True was in filter
            call_kwargs = mock_tenant_user.objects.filter.call_args[1]
            assert call_kwargs['is_admin'] is True
    
    def test_permission_non_admin_user(self):
        """Test permission denied for non-admin user."""
        permission = TenantAdminPermission()
        
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.pk = 1
        
        mock_tenant = Mock()
        mock_tenant.pk = 100
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = mock_tenant
        
        with patch('oxutils.oxiliere.permissions.TenantUser') as mock_tenant_user:
            mock_tenant_user.objects.filter.return_value.exists.return_value = False
            
            result = permission.has_permission(mock_request)
            
            assert result is False


class TestTenantUserPermission:
    """Test TenantUserPermission class."""
    
    def test_permission_tenant_member(self):
        """Test permission granted for tenant member."""
        permission = TenantUserPermission()
        
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.pk = 1
        
        mock_tenant = Mock()
        mock_tenant.pk = 100
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = mock_tenant
        
        with patch('oxutils.oxiliere.permissions.TenantUser') as mock_tenant_user:
            mock_tenant_user.objects.filter.return_value.exists.return_value = True
            
            result = permission.has_permission(mock_request)
            
            assert result is True
    
    def test_permission_non_member(self):
        """Test permission denied for non-member."""
        permission = TenantUserPermission()
        
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.pk = 1
        
        mock_tenant = Mock()
        mock_tenant.pk = 100
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = mock_tenant
        
        with patch('oxutils.oxiliere.permissions.TenantUser') as mock_tenant_user:
            mock_tenant_user.objects.filter.return_value.exists.return_value = False
            
            result = permission.has_permission(mock_request)
            
            assert result is False


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


class TestPermissionIntegration:
    """Test permission integration scenarios."""
    
    def test_multiple_permissions_hierarchy(self):
        """Test that owner permission is more restrictive than tenant permission."""
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.pk = 1
        
        mock_tenant = Mock()
        mock_tenant.pk = 100
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = mock_tenant
        
        tenant_perm = TenantPermission()
        owner_perm = TenantOwnerPermission()
        
        with patch('oxutils.oxiliere.permissions.TenantUser') as mock_tenant_user:
            # User is member but not owner
            def filter_side_effect(**kwargs):
                mock_qs = Mock()
                if 'is_owner' in kwargs:
                    mock_qs.exists.return_value = False
                else:
                    mock_qs.exists.return_value = True
                return mock_qs
            
            mock_tenant_user.objects.filter.side_effect = filter_side_effect
            
            # Should pass tenant permission
            assert tenant_perm.has_permission(mock_request) is True
            
            # Should fail owner permission
            assert owner_perm.has_permission(mock_request) is False
    
    def test_service_permission_vs_user_permission(self):
        """Test service permission works independently of user permission."""
        # Service permission with valid token
        service_perm = OxiliereServicePermission()
        token = OxilierServiceToken.for_service({'service': 'api'})
        
        mock_request = Mock()
        mock_request.headers.get.return_value = str(token)
        mock_request.META.get.return_value = None
        mock_request.user = AnonymousUser()  # No user
        
        # Service permission should pass even without user
        assert service_perm.has_permission(mock_request) is True
        
        # But tenant permission should fail
        tenant_perm = TenantPermission()
        assert tenant_perm.has_permission(mock_request) is False
    
    def test_kwargs_passed_to_permission(self):
        """Test that kwargs are properly handled by permissions."""
        permission = TenantPermission()
        
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.pk = 1
        
        mock_tenant = Mock()
        mock_tenant.pk = 100
        
        mock_request = Mock()
        mock_request.user = mock_user
        mock_request.tenant = mock_tenant
        
        with patch('oxutils.oxiliere.permissions.TenantUser') as mock_tenant_user:
            mock_tenant_user.objects.filter.return_value.exists.return_value = True
            
            # Should work with kwargs
            result = permission.has_permission(mock_request, view=Mock(), extra_param='test')
            
            assert result is True
