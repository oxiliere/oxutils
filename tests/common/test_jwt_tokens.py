"""
Tests for JWT tokens (OxilierServiceToken, OrganizationAccessToken, TokenTenant).
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from django.conf import settings
from oxutils.jwt.tokens import OxilierServiceToken, OrganizationAccessToken
from oxutils.jwt.models import TokenTenant


class TestOxilierServiceToken:
    """Test OxilierServiceToken class."""
    
    def test_service_token_creation(self):
        """Test creating a service token."""
        token = OxilierServiceToken.for_service()
        
        assert token is not None
        assert token.token_type == 'service'
        assert 'exp' in token.payload
        assert 'iat' in token.payload
    
    def test_service_token_with_payload(self):
        """Test creating a service token with custom payload."""
        custom_payload = {
            'service_name': 'auth-service',
            'permissions': ['read', 'write']
        }
        
        token = OxilierServiceToken.for_service(custom_payload)
        
        assert token['service_name'] == 'auth-service'
        assert token['permissions'] == ['read', 'write']
    
    def test_service_token_encoding(self):
        """Test encoding service token to string."""
        token = OxilierServiceToken.for_service({'service': 'test'})
        token_str = str(token)
        
        assert isinstance(token_str, str)
        assert len(token_str) > 0
        assert token_str.count('.') == 2  # JWT format
    
    def test_service_token_decoding(self):
        """Test decoding service token from string."""
        original_token = OxilierServiceToken.for_service({'service': 'test'})
        token_str = str(original_token)
        
        decoded_token = OxilierServiceToken(token=token_str)
        
        assert decoded_token['service'] == 'test'
        assert decoded_token.token_type == 'service'
    
    def test_service_token_expiration(self):
        """Test service token expiration time."""
        token = OxilierServiceToken.for_service()
        
        exp_time = datetime.fromtimestamp(token['exp'])
        iat_time = datetime.fromtimestamp(token['iat'])
        
        # Should expire in 3 minutes (default setting)
        time_diff = exp_time - iat_time
        assert time_diff.total_seconds() == 3 * 60
    
    def test_service_token_invalid(self):
        """Test invalid service token raises error."""
        with pytest.raises(Exception):
            OxilierServiceToken(token="invalid.token.string")


class TestOrganizationAccessToken:
    """Test OrganizationAccessToken class."""
    
    def test_org_token_for_tenant(self):
        """Test creating organization token for tenant."""
        mock_tenant = Mock()
        mock_tenant.id = 123
        mock_tenant.oxi_id = 'org-uuid-123'
        mock_tenant.schema_name = 'tenant_schema'
        mock_tenant.subscription_plan = 'premium'
        mock_tenant.subscription_status = 'active'
        mock_tenant.subscription_end_date = '2025-12-31'
        mock_tenant.status = 'active'
        
        token = OrganizationAccessToken.for_tenant(mock_tenant)
        
        assert token['tenant_id'] == '123'
        assert token['oxi_id'] == 'org-uuid-123'
        assert token['schema_name'] == 'tenant_schema'
        assert token['subscription_plan'] == 'premium'
        assert token['subscription_status'] == 'active'
        assert token['status'] == 'active'
    
    def test_org_token_type(self):
        """Test organization token type."""
        mock_tenant = Mock()
        mock_tenant.id = 1
        mock_tenant.oxi_id = 'test'
        mock_tenant.schema_name = 'test'
        mock_tenant.subscription_plan = 'basic'
        mock_tenant.subscription_status = 'active'
        mock_tenant.subscription_end_date = '2025-12-31'
        mock_tenant.status = 'active'
        
        token = OrganizationAccessToken.for_tenant(mock_tenant)
        
        assert token.token_type == 'org_access'
    
    def test_org_token_encoding(self):
        """Test encoding organization token."""
        mock_tenant = Mock()
        mock_tenant.id = 1
        mock_tenant.oxi_id = 'test-org'
        mock_tenant.schema_name = 'test_schema'
        mock_tenant.subscription_plan = 'basic'
        mock_tenant.subscription_status = 'active'
        mock_tenant.subscription_end_date = '2025-12-31'
        mock_tenant.status = 'active'
        
        token = OrganizationAccessToken.for_tenant(mock_tenant)
        token_str = str(token)
        
        assert isinstance(token_str, str)
        assert len(token_str) > 0
        assert token_str.count('.') == 2
    
    def test_org_token_decoding(self):
        """Test decoding organization token."""
        mock_tenant = Mock()
        mock_tenant.id = 456
        mock_tenant.oxi_id = 'org-456'
        mock_tenant.schema_name = 'org_schema'
        mock_tenant.subscription_plan = 'enterprise'
        mock_tenant.subscription_status = 'active'
        mock_tenant.subscription_end_date = '2025-12-31'
        mock_tenant.status = 'active'
        
        original_token = OrganizationAccessToken.for_tenant(mock_tenant)
        token_str = str(original_token)
        
        decoded_token = OrganizationAccessToken(token=token_str)
        
        assert decoded_token['tenant_id'] == '456'
        assert decoded_token['oxi_id'] == 'org-456'
        assert decoded_token['schema_name'] == 'org_schema'
    
    def test_org_token_expiration(self):
        """Test organization token expiration time."""
        mock_tenant = Mock()
        mock_tenant.id = 1
        mock_tenant.oxi_id = 'test'
        mock_tenant.schema_name = 'test'
        mock_tenant.subscription_plan = 'basic'
        mock_tenant.subscription_status = 'active'
        mock_tenant.subscription_end_date = '2025-12-31'
        mock_tenant.status = 'active'
        
        token = OrganizationAccessToken.for_tenant(mock_tenant)
        
        exp_time = datetime.fromtimestamp(token['exp'])
        iat_time = datetime.fromtimestamp(token['iat'])
        
        # Should expire in 60 minutes (default setting)
        time_diff = exp_time - iat_time
        assert time_diff.total_seconds() == 60 * 60


class TestTokenTenant:
    """Test TokenTenant model."""
    
    def test_token_tenant_creation(self):
        """Test creating TokenTenant instance."""
        tenant = TokenTenant(
            schema_name='test_schema',
            tenant_id=123,
            oxi_id='org-123',
            subscription_plan='premium',
            subscription_status='active',
            status='active'
        )
        
        assert tenant.schema_name == 'test_schema'
        assert tenant.id == 123
        assert tenant.oxi_id == 'org-123'
        assert tenant.subscription_plan == 'premium'
        assert tenant.subscription_status == 'active'
        assert tenant.status == 'active'
    
    def test_token_tenant_pk_property(self):
        """Test TokenTenant pk property."""
        tenant = TokenTenant(
            schema_name='test',
            tenant_id=456,
            oxi_id='org-456',
            subscription_plan='basic',
            subscription_status='active',
            status='active'
        )
        
        assert tenant.pk == 456
        assert tenant.pk == tenant.id
    
    def test_token_tenant_str(self):
        """Test TokenTenant string representation."""
        tenant = TokenTenant(
            schema_name='my_schema',
            tenant_id=1,
            oxi_id='org-uuid',
            subscription_plan='basic',
            subscription_status='active',
            status='active'
        )
        
        assert str(tenant) == 'my_schema - org-uuid'
    
    def test_token_tenant_for_token_success(self):
        """Test creating TokenTenant from valid token."""
        mock_tenant = Mock()
        mock_tenant.id = 789
        mock_tenant.oxi_id = 'org-789'
        mock_tenant.schema_name = 'tenant_789'
        mock_tenant.subscription_plan = 'enterprise'
        mock_tenant.subscription_status = 'active'
        mock_tenant.subscription_end_date = '2025-12-31'
        mock_tenant.status = 'active'
        
        # Create token
        token = OrganizationAccessToken.for_tenant(mock_tenant)
        token_str = str(token)
        
        # Create TokenTenant from token
        tenant = TokenTenant.for_token(token_str)
        
        assert tenant is not None
        assert tenant.id == '789'
        assert tenant.oxi_id == 'org-789'
        assert tenant.schema_name == 'tenant_789'
        assert tenant.subscription_plan == 'enterprise'
    
    def test_token_tenant_for_token_invalid(self):
        """Test creating TokenTenant from invalid token returns None."""
        tenant = TokenTenant.for_token("invalid.token.string")
        
        assert tenant is None
    
    def test_token_tenant_for_token_expired(self):
        """Test creating TokenTenant from expired token returns None."""
        mock_tenant = Mock()
        mock_tenant.id = 1
        mock_tenant.oxi_id = 'test'
        mock_tenant.schema_name = 'test'
        mock_tenant.subscription_plan = 'basic'
        mock_tenant.subscription_status = 'active'
        mock_tenant.subscription_end_date = '2025-12-31'
        mock_tenant.status = 'active'
        
        # Create token and manually expire it
        token = OrganizationAccessToken.for_tenant(mock_tenant)
        token.payload['exp'] = datetime.now() - timedelta(hours=1)
        token_str = str(token)
        
        # Should return None for expired token
        tenant = TokenTenant.for_token(token_str)
        
        assert tenant is None


class TestTokenIntegration:
    """Test token integration scenarios."""
    
    def test_service_token_roundtrip(self):
        """Test service token encode/decode roundtrip."""
        payload = {
            'service': 'api-gateway',
            'version': '1.0'
        }
        
        token = OxilierServiceToken.for_service(payload)
        token_str = str(token)
        decoded = OxilierServiceToken(token=token_str)
        
        assert decoded['service'] == 'api-gateway'
        assert decoded['version'] == '1.0'
    
    def test_org_token_to_tenant_model(self):
        """Test converting organization token to TokenTenant."""
        mock_tenant = Mock()
        mock_tenant.id = 999
        mock_tenant.oxi_id = 'org-999'
        mock_tenant.schema_name = 'org_999_schema'
        mock_tenant.subscription_plan = 'premium'
        mock_tenant.subscription_status = 'active'
        mock_tenant.subscription_end_date = '2025-12-31'
        mock_tenant.status = 'active'
        
        # Create token from tenant
        token = OrganizationAccessToken.for_tenant(mock_tenant)
        token_str = str(token)
        
        # Recreate tenant from token
        tenant = TokenTenant.for_token(token_str)
        
        assert tenant.id == '999'
        assert tenant.oxi_id == 'org-999'
        assert tenant.schema_name == 'org_999_schema'
        assert tenant.subscription_plan == 'premium'
    
    def test_multiple_tokens_different_data(self):
        """Test creating multiple tokens with different data."""
        mock_tenant1 = Mock()
        mock_tenant1.id = 1
        mock_tenant1.oxi_id = 'org-1'
        mock_tenant1.schema_name = 'schema_1'
        mock_tenant1.subscription_plan = 'basic'
        mock_tenant1.subscription_status = 'active'
        mock_tenant1.subscription_end_date = '2025-12-31'
        mock_tenant1.status = 'active'
        
        mock_tenant2 = Mock()
        mock_tenant2.id = 2
        mock_tenant2.oxi_id = 'org-2'
        mock_tenant2.schema_name = 'schema_2'
        mock_tenant2.subscription_plan = 'premium'
        mock_tenant2.subscription_status = 'active'
        mock_tenant2.subscription_end_date = '2025-12-31'
        mock_tenant2.status = 'active'
        
        token1 = OrganizationAccessToken.for_tenant(mock_tenant1)
        token2 = OrganizationAccessToken.for_tenant(mock_tenant2)
        
        assert token1['tenant_id'] != token2['tenant_id']
        assert token1['oxi_id'] != token2['oxi_id']
        assert token1['subscription_plan'] != token2['subscription_plan']
