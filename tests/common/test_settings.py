"""
Tests for OxUtils settings module.
"""
import pytest
import os
from oxutils.settings import OxUtilsSettings


@pytest.fixture
def clean_env(monkeypatch):
    """Remove OXI_ environment variables for clean testing."""
    # Remove all OXI_ variables
    for key in list(os.environ.keys()):
        if key.startswith('OXI_'):
            monkeypatch.delenv(key, raising=False)
    return monkeypatch


class TestOxUtilsSettings:
    """Test OxUtilsSettings configuration."""
    
    def test_settings_initialization(self):
        """Test basic settings initialization."""
        settings = OxUtilsSettings(service_name='test-service')
        assert settings.service_name == 'test-service'
    
    def test_jwt_default_values(self):
        """Test JWT default values."""
        settings = OxUtilsSettings(service_name='test')
        assert settings.jwt_access_token_key == 'access'
        assert settings.jwt_org_access_token_key == 'org_access'
        assert settings.jwt_signing_key is None
        assert settings.jwt_verifying_key is None
    
    def test_audit_default_values(self):
        """Test audit default values."""
        settings = OxUtilsSettings(service_name='test')
        assert settings.log_access is False
        assert settings.retention_delay == 7
    
    
    def test_jwt_key_validation_file_not_found(self, tmp_path):
        """Test JWT key validation fails if file doesn't exist."""
        with pytest.raises(ValueError, match="JWT verifying key file not found"):
            OxUtilsSettings(
                service_name='test',
                jwt_verifying_key='/nonexistent/path/key.pem',
            )
    
    def test_jwt_key_validation_success(self, temp_jwt_key):
        """Test JWT key validation succeeds with valid file."""
        settings = OxUtilsSettings(
            service_name='test',
            jwt_verifying_key=temp_jwt_key['public_key_path'],
        )
        assert settings.jwt_verifying_key == temp_jwt_key['public_key_path']
    
    def test_env_prefix(self, monkeypatch):
        """Test environment variable prefix."""
        monkeypatch.setenv('OXI_SERVICE_NAME', 'env-service')
        monkeypatch.setenv('OXI_LOG_ACCESS', 'true')
        monkeypatch.setenv('OXI_RETENTION_DELAY', '30')
        
        settings = OxUtilsSettings()
        assert settings.service_name == 'env-service'
        assert settings.log_access is True
        assert settings.retention_delay == 30
