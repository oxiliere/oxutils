"""
Tests for oxutils.auth.app_settings module.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch


class TestAppSettings:
    """Tests for app_settings module - validates the serializer lookup logic."""

    def test_import_callable_used_for_resolution(self):
        from oxutils.auth.utils import import_callable
        import json

        result = import_callable("json.dumps")
        assert result is json.dumps

    @patch("oxutils.auth.app_settings.settings")
    def test_schemas_dict_fallback_to_default(self, mock_settings):
        """When JWT_ALLAUTH_SCHEMAS is empty, default classes are used."""
        mock_settings.JWT_ALLAUTH_SCHEMAS = {}
        import importlib
        import oxutils.auth.app_settings

        importlib.reload(oxutils.auth.app_settings)
        from oxutils.auth.app_settings import LoginSerializer
        from oxutils.auth.schemas import LoginSchema

        # Default LoginSerializer should be the LoginSchema class itself
        assert LoginSerializer is LoginSchema
