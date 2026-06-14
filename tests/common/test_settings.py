"""
Tests for OxUtils settings module.
"""

import os

import pytest

from oxutils.settings import OxUtilsSettings


@pytest.fixture
def clean_env(monkeypatch):
    for key in list(os.environ.keys()):
        if key.startswith("OXI_"):
            monkeypatch.delenv(key, raising=False)
    return monkeypatch


class TestOxUtilsSettings:
    """Test OxUtilsSettings — only behavior that can break."""

    def test_jwt_key_validation_file_not_found(self, tmp_path):
        with pytest.raises(ValueError, match="JWT verifying key file not found"):
            OxUtilsSettings(
                service_name="test",
                jwt_verifying_key="/nonexistent/path/key.pem",
            )

    def test_jwt_key_validation_success(self, temp_jwt_key):
        settings = OxUtilsSettings(
            service_name="test",
            jwt_verifying_key=temp_jwt_key["public_key_path"],
        )
        assert settings.jwt_verifying_key == temp_jwt_key["public_key_path"]

    def test_env_prefix(self, monkeypatch):
        monkeypatch.setenv("OXI_SERVICE_NAME", "env-service")
        monkeypatch.setenv("OXI_LOG_ACCESS", "true")
        monkeypatch.setenv("OXI_RETENTION_DELAY", "30")

        settings = OxUtilsSettings()
        assert settings.service_name == "env-service"
        assert settings.log_access is True
        assert settings.retention_delay == 30
