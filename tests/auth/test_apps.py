"""
Tests for oxutils.auth.apps module.
"""
import pytest

from oxutils.auth.apps import OxiAuthConfig


class TestOxiAuthConfig:
    """Tests for OxiAuthConfig Django app config."""

    def test_app_name(self):
        assert OxiAuthConfig.name == "oxutils.auth"

    def test_app_label(self):
        assert OxiAuthConfig.label == "oxi_auth"

    def test_is_django_app_config(self):
        from django.apps import AppConfig

        assert issubclass(OxiAuthConfig, AppConfig)
