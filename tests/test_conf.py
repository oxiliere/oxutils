"""
Tests for oxutils configuration.
"""
import pytest
from oxutils.conf import UTILS_APPS, AUDIT_MIDDLEWARE


class TestConfiguration:
    """Test oxutils configuration constants."""

    def test_utils_apps_contains_audit(self):
        """Test that UTILS_APPS includes oxutils.audit."""
        assert 'oxutils.audit' in UTILS_APPS

    def test_utils_apps_contains_required_apps(self):
        """Test that UTILS_APPS contains all required applications."""
        required_apps = [
            'django_structlog',
            'auditlog',
            'django_celery_results',
            'oxutils.audit',
        ]
        
        for app in required_apps:
            assert app in UTILS_APPS, f"{app} should be in UTILS_APPS"
    
    def test_utils_apps_count(self):
        """Test that UTILS_APPS has the expected number of apps."""
        assert len(UTILS_APPS) == 4

    def test_audit_middleware_contains_required(self):
        """Test that AUDIT_MIDDLEWARE contains required middleware."""
        required_middleware = [
            'auditlog.middleware.AuditlogMiddleware',
            'django_structlog.middlewares.RequestMiddleware',
        ]
        
        for middleware in required_middleware:
            assert middleware in AUDIT_MIDDLEWARE, f"{middleware} should be in AUDIT_MIDDLEWARE"

    def test_utils_apps_is_tuple(self):
        """Test that UTILS_APPS is a tuple."""
        assert isinstance(UTILS_APPS, tuple)

    def test_audit_middleware_is_tuple(self):
        """Test that AUDIT_MIDDLEWARE is a tuple."""
        assert isinstance(AUDIT_MIDDLEWARE, tuple)
