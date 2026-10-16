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

    def test_jwt_key_validation_invalid_base64(self):
        with pytest.raises(ValueError, match="JWT verifying key is not a valid base64"):
            OxUtilsSettings(
                service_name="test",
                jwt_verifying_key="not-valid-base64!!",
            )

    def test_jwt_key_validation_success(self, temp_jwt_key):
        settings = OxUtilsSettings(
            service_name="test",
            jwt_verifying_key=temp_jwt_key["public_key_b64"],
        )
        assert settings.jwt_verifying_key == temp_jwt_key["public_key_b64"]
        assert settings.jwt_verifying_key_pem == temp_jwt_key["public_key_pem"]

    def test_jwt_key_decoded_property_is_none_when_unset(self):
        settings = OxUtilsSettings(service_name="test")
        assert settings.jwt_verifying_key_pem is None
        assert settings.jwt_signing_key_pem is None

    def test_env_prefix(self, monkeypatch):
        monkeypatch.setenv("OXI_SERVICE_NAME", "env-service")
        monkeypatch.setenv("OXI_LOG_ACCESS", "true")
        monkeypatch.setenv("OXI_RETENTION_DELAY", "30")

        settings = OxUtilsSettings()
        assert settings.service_name == "env-service"
        assert settings.log_access is True
        assert settings.retention_delay == 30
