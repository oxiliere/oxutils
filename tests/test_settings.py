"""
Tests for OxUtils settings module.
"""
import pytest
import os
from pydantic import ValidationError
from oxutils.settings import OxUtilsSettings, oxi_settings


class TestOxUtilsSettings:
    """Test OxUtilsSettings configuration."""
    
    def test_settings_initialization(self):
        """Test basic settings initialization."""
        settings = OxUtilsSettings(service_name='test-service')
        assert settings.service_name == 'test-service'
    
    def test_jwt_default_values(self):
        """Test JWT default values."""
        settings = OxUtilsSettings(service_name='test')
        assert settings.jwt_access_token_key == 'access_token'
        assert settings.jwt_org_access_token_key == 'org_access_token'
        assert settings.jwt_signing_key is None
        assert settings.jwt_verifying_key is None
    
    def test_audit_default_values(self):
        """Test audit default values."""
        settings = OxUtilsSettings(service_name='test')
        assert settings.log_access is False
        assert settings.retention_delay == 7
    
    def test_s3_default_values(self):
        """Test S3 default values."""
        settings = OxUtilsSettings(service_name='test')
        assert settings.use_static_s3 is False
        assert settings.use_default_s3 is False
        assert settings.use_private_s3 is False
        assert settings.use_log_s3 is False
        assert settings.static_default_acl == 'public-read'
        assert settings.private_s3_default_acl == 'private'
    
    def test_s3_validation_missing_credentials(self):
        """Test S3 validation fails with missing credentials."""
        with pytest.raises(ValueError, match="Missing required static S3 configuration"):
            OxUtilsSettings(
                service_name='test',
                use_static_s3=True,
                # Missing credentials
            )
    
    def test_s3_validation_success(self):
        """Test S3 validation succeeds with all credentials."""
        settings = OxUtilsSettings(
            service_name='test',
            use_static_s3=True,
            static_access_key_id='test-key',
            static_secret_access_key='test-secret',
            static_storage_bucket_name='test-bucket',
            static_s3_custom_domain='cdn.example.com',
        )
        assert settings.use_static_s3 is True
    
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
    
    def test_use_static_s3_as_default_validation(self):
        """Test validation for use_static_s3_as_default."""
        with pytest.raises(ValueError, match="OXI_USE_STATIC_S3_AS_DEFAULT requires"):
            OxUtilsSettings(
                service_name='test',
                use_default_s3=True,
                use_static_s3_as_default=True,
                use_static_s3=False,  # Should fail
            )
    
    def test_use_private_s3_as_log_validation(self):
        """Test validation for use_private_s3_as_log."""
        with pytest.raises(ValueError, match="OXI_USE_PRIVATE_S3_AS_LOG requires"):
            OxUtilsSettings(
                service_name='test',
                use_log_s3=True,
                use_private_s3_as_log=True,
                use_private_s3=False,  # Should fail
            )
    
    def test_get_static_storage_url(self):
        """Test get_static_storage_url method."""
        settings = OxUtilsSettings(
            service_name='test',
            use_static_s3=True,
            static_access_key_id='key',
            static_secret_access_key='secret',
            static_storage_bucket_name='bucket',
            static_s3_custom_domain='cdn.example.com',
            static_location='static',
        )
        url = settings.get_static_storage_url()
        assert url == 'https://cdn.example.com/static/'
    
    def test_get_default_storage_url(self):
        """Test get_default_storage_url method."""
        settings = OxUtilsSettings(
            service_name='test',
            use_default_s3=True,
            default_s3_access_key_id='key',
            default_s3_secret_access_key='secret',
            default_s3_storage_bucket_name='bucket',
            default_s3_s3_custom_domain='cdn.example.com',
            default_s3_location='media',
        )
        url = settings.get_default_storage_url()
        assert url == 'https://cdn.example.com/media/'
    
    def test_get_log_storage_url(self):
        """Test get_log_storage_url method."""
        settings = OxUtilsSettings(
            service_name='test-service',
            use_log_s3=True,
            log_s3_access_key_id='key',
            log_s3_secret_access_key='secret',
            log_s3_storage_bucket_name='bucket',
            log_s3_s3_custom_domain='logs.example.com',
            log_s3_location='oxi_logs',
        )
        url = settings.get_log_storage_url()
        assert url == 'https://logs.example.com/oxi_logs/test-service/'
    
    def test_env_prefix(self, monkeypatch):
        """Test environment variable prefix."""
        monkeypatch.setenv('OXI_SERVICE_NAME', 'env-service')
        monkeypatch.setenv('OXI_LOG_ACCESS', 'true')
        monkeypatch.setenv('OXI_RETENTION_DELAY', '30')
        
        settings = OxUtilsSettings()
        assert settings.service_name == 'env-service'
        assert settings.log_access is True
        assert settings.retention_delay == 30


class TestWriteDjangoSettings:
    """Test write_django_settings method."""
    
    def test_write_static_settings(self):
        """Test writing static S3 settings to Django."""
        from types import ModuleType
        django_settings = ModuleType('settings')
        
        settings = OxUtilsSettings(
            service_name='test',
            use_static_s3=True,
            static_access_key_id='key',
            static_secret_access_key='secret',
            static_storage_bucket_name='bucket',
            static_s3_custom_domain='cdn.example.com',
        )
        
        settings.write_django_settings(django_settings)
        
        assert hasattr(django_settings, 'STATIC_URL')
        assert hasattr(django_settings, 'STATICFILES_STORAGE')
        assert django_settings.STATIC_URL == 'https://cdn.example.com/static/'
    
    def test_write_media_settings(self):
        """Test writing media S3 settings to Django."""
        from types import ModuleType
        django_settings = ModuleType('settings')
        
        settings = OxUtilsSettings(
            service_name='test',
            use_default_s3=True,
            default_s3_access_key_id='key',
            default_s3_secret_access_key='secret',
            default_s3_storage_bucket_name='bucket',
            default_s3_s3_custom_domain='cdn.example.com',
        )
        
        settings.write_django_settings(django_settings)
        
        assert hasattr(django_settings, 'MEDIA_URL')
        assert hasattr(django_settings, 'DEFAULT_FILE_STORAGE')
        assert django_settings.MEDIA_URL == 'https://cdn.example.com/media/'
    
    def test_write_private_settings(self):
        """Test writing private S3 settings to Django."""
        from types import ModuleType
        django_settings = ModuleType('settings')
        
        settings = OxUtilsSettings(
            service_name='test',
            use_private_s3=True,
            private_s3_access_key_id='key',
            private_s3_secret_access_key='secret',
            private_s3_storage_bucket_name='bucket',
            private_s3_s3_custom_domain='private.example.com',
        )
        
        settings.write_django_settings(django_settings)
        
        assert hasattr(django_settings, 'PRIVATE_MEDIA_LOCATION')
        assert hasattr(django_settings, 'PRIVATE_FILE_STORAGE')
        assert django_settings.PRIVATE_MEDIA_LOCATION == 'private'
