"""
Tests for Oxiliere multi-tenant module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from django.test import TestCase, RequestFactory, override_settings
from django.http import Http404, HttpResponseBadRequest
from django.contrib.auth import get_user_model
from django.db import connection


@pytest.mark.django_db
class TestOxidToSchemaName(TestCase):
    """Tests for oxid_to_schema_name utility function."""

    def test_simple_conversion(self):
        """Test simple organization ID conversion."""
        from oxutils.oxiliere.utils import oxid_to_schema_name
        
        schema_name = oxid_to_schema_name('acme-corp')
        
        assert schema_name == 'tenant_acme_corp'

    def test_with_numbers(self):
        """Test conversion with numbers."""
        from oxutils.oxiliere.utils import oxid_to_schema_name
        
        schema_name = oxid_to_schema_name('company-123')
        
        assert schema_name == 'tenant_company_123'

    def test_with_special_characters(self):
        """Test conversion removes special characters."""
        from oxutils.oxiliere.utils import oxid_to_schema_name
        
        schema_name = oxid_to_schema_name('my-company@2024!')
        
        assert schema_name == 'tenant_my_company2024'

    def test_uppercase_to_lowercase(self):
        """Test uppercase conversion to lowercase."""
        from oxutils.oxiliere.utils import oxid_to_schema_name
        
        schema_name = oxid_to_schema_name('ACME-CORP')
        
        assert schema_name == 'tenant_acme_corp'

    def test_multiple_hyphens(self):
        """Test multiple hyphens conversion."""
        from oxutils.oxiliere.utils import oxid_to_schema_name
        
        schema_name = oxid_to_schema_name('my-big-company-name')
        
        assert schema_name == 'tenant_my_big_company_name'

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        from oxutils.oxiliere.utils import oxid_to_schema_name
        
        with pytest.raises(ValueError) as exc_info:
            oxid_to_schema_name('')
        
        assert "oxi_id cannot be empty" in str(exc_info.value)

    def test_too_long_name_raises_error(self):
        """Test that too long name raises ValueError."""
        from oxutils.oxiliere.utils import oxid_to_schema_name
        
        # Create a very long ID (more than 55 chars after tenant_ prefix)
        long_id = 'a' * 60
        
        with pytest.raises(ValueError) as exc_info:
            oxid_to_schema_name(long_id)
        
        assert "Schema name too long" in str(exc_info.value)

    def test_prefix_added(self):
        """Test that tenant_ prefix is always added."""
        from oxutils.oxiliere.utils import oxid_to_schema_name
        
        schema_name = oxid_to_schema_name('test')
        
        assert schema_name.startswith('tenant_')


@pytest.mark.django_db
class TestTenantMainMiddleware(TestCase):
    """Tests for TenantMainMiddleware."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.middleware = self._get_middleware()

    def _get_middleware(self):
        """Get middleware instance."""
        from oxutils.oxiliere.middleware import TenantMainMiddleware
        return TenantMainMiddleware(get_response=lambda r: None)

    def test_get_org_id_from_header(self):
        """Test organization ID extraction from header."""
        request = self.factory.get('/', HTTP_X_ORGANIZATION_ID='acme-corp')
        
        org_id = self.middleware.get_org_id_from_request(request)
        
        assert org_id == 'acme-corp'

    def test_get_org_id_from_meta(self):
        """Test organization ID extraction from META."""
        request = self.factory.get('/')
        request.META['HTTP_X_ORGANIZATION_ID'] = 'test-org'
        
        org_id = self.middleware.get_org_id_from_request(request)
        
        assert org_id == 'test-org'

    @patch('oxutils.oxiliere.middleware.connection')
    def test_missing_org_id_returns_bad_request(self, mock_connection):
        """Test that missing organization ID returns 400."""
        mock_connection.set_schema_to_public = Mock()
        
        request = self.factory.get('/')
        response = self.middleware.process_request(request)
        
        assert isinstance(response, HttpResponseBadRequest)
        assert 'Missing X-Organization-ID header' in str(response.content)

    @patch('oxutils.oxiliere.middleware.connection')
    def test_tenant_not_found_raises_404(self, mock_connection):
        """Test that non-existent tenant raises 404."""
        from django.http import Http404
        
        mock_connection.set_schema_to_public = Mock()
        mock_connection.tenant_model = Mock()
        mock_connection.tenant_model.DoesNotExist = Http404
        
        request = self.factory.get('/', HTTP_X_ORGANIZATION_ID='nonexistent')
        request.user = Mock()  # Add user attribute
        
        with patch.object(self.middleware, 'get_tenant') as mock_get_tenant:
            mock_get_tenant.side_effect = Http404
            
            with pytest.raises(Http404):
                self.middleware.process_request(request)

    @patch('oxutils.oxiliere.middleware.connection')
    def test_successful_tenant_switch(self, mock_connection):
        """Test successful tenant schema switch."""
        from django.contrib.auth.models import AnonymousUser
        from oxutils.jwt.models import TokenTenant
        
        mock_connection.set_schema_to_public = Mock()
        
        # Create a real class for tenant_model and mock_tenant so isinstance works
        TenantModel = type('TenantModel', (), {})
        mock_connection.tenant_model = TenantModel
        mock_connection.set_tenant = Mock()
        
        # Create mock_tenant as instance of TenantModel so isinstance works
        mock_tenant = Mock(spec=TenantModel)
        mock_tenant.id = "test-id"
        mock_tenant.oxi_id = 'acme-corp'
        mock_tenant.schema_name = 'tenant_acmecorp'
        mock_tenant.is_deleted = False
        mock_tenant.is_active = True
        mock_tenant.subscription_plan = 'basic'
        mock_tenant.subscription_status = 'active'
        mock_tenant.subscription_end_date = '2025-12-31'
        mock_tenant.status = 'active'
        
        request = self.factory.get('/', HTTP_X_ORGANIZATION_ID='acme-corp')
        request.user = AnonymousUser()  # Add user attribute
        
        with patch.object(self.middleware, 'get_tenant', return_value=mock_tenant):
            with patch.object(self.middleware, 'get_tenant_user', return_value=Mock()):
                with patch.object(self.middleware, 'setup_url_routing'):
                    with patch('oxutils.oxiliere.middleware.set_current_tenant_schema_name'):
                        self.middleware.process_request(request)
        
        # Check that request.tenant is now a TokenTenant (not the original mock)
        assert isinstance(request.tenant, TokenTenant)
        assert request.tenant.oxi_id == 'acme-corp'
        assert request.tenant.schema_name == 'tenant_acmecorp'
        
        # Check that request.db_tenant is the original DB tenant
        assert request.db_tenant == mock_tenant


@pytest.mark.django_db
class TestTenantPermissions(TestCase):
    """Tests for tenant permission classes."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = Mock()
        self.user.is_authenticated = True
        self.tenant = Mock()
        self.tenant.oxi_id = 'test-tenant'

    @pytest.mark.skipif(True, reason="ninja.permissions module not available in test environment")
    def test_tenant_permission_placeholder(self):
        """Placeholder for permission tests - requires ninja.permissions."""
        pass


@pytest.mark.django_db
class TestUpdateTenantUtils(TestCase):
    """Tests for tenant update utilities."""

    @pytest.mark.skipif(True, reason="update_tenant requires cacheops which is not available in test environment")
    def test_update_tenant_placeholder(self):
        """Placeholder for update_tenant tests - requires cacheops."""
        pass


@pytest.mark.django_db
class TestCreateTenantSchema(TestCase):
    """Tests for CreateTenantSchema."""

    @pytest.mark.skipif(True, reason="schemas module requires ninja which is not available in test environment")
    def test_create_tenant_placeholder(self):
        """Placeholder for schema tests - requires ninja schemas."""
        pass


@pytest.mark.django_db
class TestTenantCaches(TestCase):
    """Tests for tenant caching functions."""

    @pytest.mark.skipif(True, reason="caches module requires cacheops which is not available in test environment")
    def test_caches_placeholder(self):
        """Placeholder for cache tests - requires cacheops."""
        pass


@pytest.mark.django_db
class TestSetupController(TestCase):
    """Tests for SetupController API."""

    @pytest.mark.skipif(True, reason="controllers module requires ninja_extra which is not available in test environment")
    def test_controller_placeholder(self):
        """Placeholder for controller tests - requires ninja_extra."""
        pass
