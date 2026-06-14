"""
Tests for TenantMainMiddleware — status handling.
"""

import json
from unittest.mock import Mock, patch

import pytest

from oxutils.oxiliere.enums import TenantStatus
from oxutils.oxiliere.middleware import TenantMainMiddleware


@pytest.fixture
def middleware():
    """Minimal middleware instance — no DB, no tenant model."""
    with patch.object(TenantMainMiddleware, "__init__", lambda self: None):
        mw = TenantMainMiddleware.__new__(TenantMainMiddleware)
        mw.tenant_model = Mock()
        return mw


def _mock_tenant(status):
    """Create a mock tenant with the given status."""
    tenant = Mock()
    tenant.status = status
    tenant.is_deleted = False
    tenant.is_active = True
    return tenant


class TestTenantStatusResponses:
    """Test the static response builders — pure functions, no DB."""

    def test_pending_migration_returns_503(self):
        response = TenantMainMiddleware._pending_migration_response("org-1")
        assert response.status_code == 503
        assert response["Retry-After"] == "30"
        body = json.loads(response.content)
        assert body["code"] == "pending_setup"

    def test_suspended_returns_423(self):
        response = TenantMainMiddleware._suspended_response("org-1")
        assert response.status_code == 423
        body = json.loads(response.content)
        assert body["code"] == "locked"

    def test_inactive_returns_404(self):
        response = TenantMainMiddleware._inactive_response("org-1")
        assert response.status_code == 404
        body = json.loads(response.content)
        assert body["code"] == "inactive"


class TestHandleTenantStatus:
    """Test _handle_tenant_status dispatch."""

    def test_active_tenant_proceeds_normally(self, middleware):
        request = Mock()
        middleware.get_org_id_from_request = Mock(return_value="org-active")
        tenant = _mock_tenant(TenantStatus.ACTIVE)

        result = middleware._handle_tenant_status(request, tenant)
        assert result is None

    def test_pending_migration_dispatches(self, middleware):
        request = Mock()
        middleware.get_org_id_from_request = Mock(return_value="org-pending")
        tenant = _mock_tenant(TenantStatus.PENDING_MIGRATION)

        result = middleware._handle_tenant_status(request, tenant)
        assert result.status_code == 503

    def test_suspended_dispatches(self, middleware):
        request = Mock()
        middleware.get_org_id_from_request = Mock(return_value="org-suspended")
        tenant = _mock_tenant(TenantStatus.SUSPENDED)

        result = middleware._handle_tenant_status(request, tenant)
        assert result.status_code == 423

    def test_inactive_dispatches(self, middleware):
        request = Mock()
        middleware.get_org_id_from_request = Mock(return_value="org-inactive")
        tenant = _mock_tenant(TenantStatus.INACTIVE)

        result = middleware._handle_tenant_status(request, tenant)
        assert result.status_code == 404

    def test_unknown_status_proceeds(self, middleware):
        """Custom / future status should not block (None = pass through)."""
        request = Mock()
        middleware.get_org_id_from_request = Mock(return_value="org-unknown")
        tenant = _mock_tenant("some_future_status")

        result = middleware._handle_tenant_status(request, tenant)
        assert result is None
