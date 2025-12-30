"""
Tests for OxUtils S3 module.
"""
import pytest
from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured


class TestStaticStorage:
    """Test StaticStorage class."""
    
    def test_static_storage_initialization_success(self):
        """Test StaticStorage initialization with valid settings."""
        with patch('oxutils.s3.storages.oxi_settings') as mock_settings:
            mock_settings.use_static_s3 = True
            mock_settings.static_access_key_id = 'test-access-key'
            mock_settings.static_secret_access_key = 'test-secret-key'
            mock_settings.static_storage_bucket_name = 'test-bucket'
            mock_settings.static_s3_custom_domain = 'test-bucket.s3.amazonaws.com'
            mock_settings.static_location = 'static'
            mock_settings.static_default_acl = 'public-read'
            
            with patch('oxutils.s3.storages.S3Boto3Storage.__init__', return_value=None):
                from oxutils.s3.storages import StaticStorage
                
                storage = StaticStorage()
                
                assert storage.access_key == 'test-access-key'
                assert storage.secret_key == 'test-secret-key'
                assert storage.bucket_name == 'test-bucket'
                assert storage.custom_domain == 'test-bucket.s3.amazonaws.com'
                assert storage.location == 'static'
                assert storage.default_acl == 'public-read'
                assert storage.file_overwrite is False
    
    def test_static_storage_not_enabled(self):
        """Test StaticStorage raises error when not enabled."""
        with patch('oxutils.s3.storages.oxi_settings') as mock_settings:
            mock_settings.use_static_s3 = False
            
            from oxutils.s3.storages import StaticStorage
            
            with pytest.raises(ImproperlyConfigured, match="StaticStorage requires OXI_USE_STATIC_S3=True"):
                StaticStorage()
    
    def test_static_storage_missing_access_key(self):
        """Test StaticStorage raises error when access key is missing."""
        with patch('oxutils.s3.storages.oxi_settings') as mock_settings:
            mock_settings.use_static_s3 = True
            mock_settings.static_access_key_id = None
            mock_settings.static_secret_access_key = 'test-secret-key'
            mock_settings.static_storage_bucket_name = 'test-bucket'
            mock_settings.static_s3_custom_domain = 'test-bucket.s3.amazonaws.com'
            
            from oxutils.s3.storages import StaticStorage
            
            with pytest.raises(ImproperlyConfigured, match="missing required configuration: access_key"):
                StaticStorage()
    
    def test_static_storage_missing_multiple_fields(self):
        """Test StaticStorage raises error when multiple fields are missing."""
        with patch('oxutils.s3.storages.oxi_settings') as mock_settings:
            mock_settings.use_static_s3 = True
            mock_settings.static_access_key_id = None
            mock_settings.static_secret_access_key = None
            mock_settings.static_storage_bucket_name = 'test-bucket'
            mock_settings.static_s3_custom_domain = 'test-bucket.s3.amazonaws.com'
            
            from oxutils.s3.storages import StaticStorage
            
            with pytest.raises(ImproperlyConfigured, match="missing required configuration"):
                StaticStorage()


class TestPublicMediaStorage:
    """Test PublicMediaStorage class."""
    
    def test_public_media_storage_with_default_s3(self):
        """Test PublicMediaStorage initialization with default S3 settings."""
        with patch('oxutils.s3.storages.oxi_settings') as mock_settings:
            mock_settings.use_default_s3 = True
            mock_settings.use_static_s3_as_default = False
            mock_settings.default_s3_access_key_id = 'default-access-key'
            mock_settings.default_s3_secret_access_key = 'default-secret-key'
            mock_settings.default_s3_storage_bucket_name = 'default-bucket'
            mock_settings.default_s3_custom_domain = 'default-bucket.s3.amazonaws.com'
            mock_settings.default_s3_location = 'media'
            mock_settings.default_s3_default_acl = 'public-read'
            
            with patch('oxutils.s3.storages.S3Boto3Storage.__init__', return_value=None):
                from oxutils.s3.storages import PublicMediaStorage
                
                storage = PublicMediaStorage()
                
                assert storage.access_key == 'default-access-key'
                assert storage.secret_key == 'default-secret-key'
                assert storage.bucket_name == 'default-bucket'
                assert storage.location == 'media'
                assert storage.file_overwrite is False
    
    def test_public_media_storage_with_static_as_default(self):
        """Test PublicMediaStorage using static S3 as default."""
        with patch('oxutils.s3.storages.oxi_settings') as mock_settings:
            mock_settings.use_default_s3 = True
            mock_settings.use_static_s3_as_default = True
            mock_settings.static_access_key_id = 'static-access-key'
            mock_settings.static_secret_access_key = 'static-secret-key'
            mock_settings.static_storage_bucket_name = 'static-bucket'
            mock_settings.static_s3_custom_domain = 'static-bucket.s3.amazonaws.com'
            mock_settings.default_s3_location = 'media'
            mock_settings.default_s3_default_acl = 'public-read'
            
            with patch('oxutils.s3.storages.S3Boto3Storage.__init__', return_value=None):
                from oxutils.s3.storages import PublicMediaStorage
                
                storage = PublicMediaStorage()
                
                assert storage.access_key == 'static-access-key'
                assert storage.secret_key == 'static-secret-key'
                assert storage.bucket_name == 'static-bucket'
    
    def test_public_media_storage_not_enabled(self):
        """Test PublicMediaStorage raises error when not enabled."""
        with patch('oxutils.s3.storages.oxi_settings') as mock_settings:
            mock_settings.use_default_s3 = False
            
            from oxutils.s3.storages import PublicMediaStorage
            
            with pytest.raises(ImproperlyConfigured, match="PublicMediaStorage requires OXI_USE_DEFAULT_S3=True"):
                PublicMediaStorage()


class TestPrivateMediaStorage:
    """Test PrivateMediaStorage class."""
    
    def test_private_media_storage_initialization(self):
        """Test PrivateMediaStorage initialization with valid settings."""
        with patch('oxutils.s3.storages.oxi_settings') as mock_settings:
            mock_settings.use_private_s3 = True
            mock_settings.private_s3_access_key_id = 'private-access-key'
            mock_settings.private_s3_secret_access_key = 'private-secret-key'
            mock_settings.private_s3_storage_bucket_name = 'private-bucket'
            mock_settings.private_s3_custom_domain = 'private-bucket.s3.amazonaws.com'
            mock_settings.private_s3_location = 'private'
            mock_settings.private_s3_default_acl = 'private'
            
            with patch('oxutils.s3.storages.S3Boto3Storage.__init__', return_value=None):
                from oxutils.s3.storages import PrivateMediaStorage
                
                storage = PrivateMediaStorage()
                
                assert storage.access_key == 'private-access-key'
                assert storage.secret_key == 'private-secret-key'
                assert storage.bucket_name == 'private-bucket'
                assert storage.location == 'private'
                assert storage.default_acl == 'private'
                assert storage.file_overwrite is False
                assert storage.querystring_auth is True
                assert storage.querystring_expire == 3600
    
    def test_private_media_storage_not_enabled(self):
        """Test PrivateMediaStorage raises error when not enabled."""
        with patch('oxutils.s3.storages.oxi_settings') as mock_settings:
            mock_settings.use_private_s3 = False
            
            from oxutils.s3.storages import PrivateMediaStorage
            
            with pytest.raises(ImproperlyConfigured, match="PrivateMediaStorage requires OXI_USE_PRIVATE_S3=True"):
                PrivateMediaStorage()


class TestLogStorage:
    """Test LogStorage class."""
    
    def test_log_storage_with_dedicated_log_s3(self):
        """Test LogStorage initialization with dedicated log S3 settings."""
        with patch('oxutils.s3.storages.oxi_settings') as mock_settings:
            mock_settings.use_log_s3 = True
            mock_settings.use_private_s3_as_log = False
            mock_settings.log_s3_access_key_id = 'log-access-key'
            mock_settings.log_s3_secret_access_key = 'log-secret-key'
            mock_settings.log_s3_storage_bucket_name = 'log-bucket'
            mock_settings.log_s3_custom_domain = 'log-bucket.s3.amazonaws.com'
            mock_settings.log_s3_location = 'logs'
            mock_settings.log_s3_default_acl = 'private'
            mock_settings.service_name = 'test-service'
            
            with patch('oxutils.s3.storages.S3Boto3Storage.__init__', return_value=None):
                from oxutils.s3.storages import LogStorage
                
                storage = LogStorage()
                
                assert storage.access_key == 'log-access-key'
                assert storage.secret_key == 'log-secret-key'
                assert storage.bucket_name == 'log-bucket'
                assert storage.location == 'logs/test-service'
                assert storage.querystring_auth is True
                assert storage.querystring_expire == 3600
    
    def test_log_storage_with_private_as_log(self):
        """Test LogStorage using private S3 as log storage."""
        with patch('oxutils.s3.storages.oxi_settings') as mock_settings:
            mock_settings.use_log_s3 = True
            mock_settings.use_private_s3_as_log = True
            mock_settings.private_s3_access_key_id = 'private-access-key'
            mock_settings.private_s3_secret_access_key = 'private-secret-key'
            mock_settings.private_s3_storage_bucket_name = 'private-bucket'
            mock_settings.private_s3_custom_domain = 'private-bucket.s3.amazonaws.com'
            mock_settings.log_s3_location = 'logs'
            mock_settings.log_s3_default_acl = 'private'
            mock_settings.service_name = 'test-service'
            
            with patch('oxutils.s3.storages.S3Boto3Storage.__init__', return_value=None):
                from oxutils.s3.storages import LogStorage
                
                storage = LogStorage()
                
                assert storage.access_key == 'private-access-key'
                assert storage.secret_key == 'private-secret-key'
                assert storage.bucket_name == 'private-bucket'
    
    def test_log_storage_not_enabled(self):
        """Test LogStorage raises error when not enabled."""
        with patch('oxutils.s3.storages.oxi_settings') as mock_settings:
            mock_settings.use_log_s3 = False
            
            from oxutils.s3.storages import LogStorage
            
            with pytest.raises(ImproperlyConfigured, match="LogStorage requires OXI_USE_LOG_S3=True"):
                LogStorage()


class TestValidateRequiredFields:
    """Test _validate_required_fields static method."""
    
    def test_validate_all_fields_present(self):
        """Test validation passes when all fields are present."""
        from oxutils.s3.storages import StaticStorage
        
        fields = {
            'access_key': 'test-key',
            'secret_key': 'test-secret',
            'bucket_name': 'test-bucket',
            'custom_domain': 'test-domain',
        }
        
        # Should not raise
        StaticStorage._validate_required_fields('TestStorage', fields)
    
    def test_validate_missing_single_field(self):
        """Test validation fails when a field is missing."""
        from oxutils.s3.storages import StaticStorage
        
        fields = {
            'access_key': 'test-key',
            'secret_key': None,
            'bucket_name': 'test-bucket',
            'custom_domain': 'test-domain',
        }
        
        with pytest.raises(ImproperlyConfigured, match="TestStorage is missing required configuration: secret_key"):
            StaticStorage._validate_required_fields('TestStorage', fields)
    
    def test_validate_missing_multiple_fields(self):
        """Test validation fails when multiple fields are missing."""
        from oxutils.s3.storages import StaticStorage
        
        fields = {
            'access_key': None,
            'secret_key': None,
            'bucket_name': 'test-bucket',
            'custom_domain': None,
        }
        
        with pytest.raises(ImproperlyConfigured, match="TestStorage is missing required configuration"):
            StaticStorage._validate_required_fields('TestStorage', fields)
    
    def test_validate_empty_string_treated_as_missing(self):
        """Test validation treats empty strings as missing."""
        from oxutils.s3.storages import StaticStorage
        
        fields = {
            'access_key': '',
            'secret_key': 'test-secret',
            'bucket_name': 'test-bucket',
            'custom_domain': 'test-domain',
        }
        
        with pytest.raises(ImproperlyConfigured, match="access_key"):
            StaticStorage._validate_required_fields('TestStorage', fields)


class TestS3StorageIntegration:
    """Test S3 storage integration scenarios."""
    
    def test_all_storage_classes_exist(self):
        """Test that all storage classes are importable."""
        from oxutils.s3.storages import (
            StaticStorage,
            PublicMediaStorage,
            PrivateMediaStorage,
            LogStorage
        )
        
        assert StaticStorage is not None
        assert PublicMediaStorage is not None
        assert PrivateMediaStorage is not None
        assert LogStorage is not None
    
    def test_storage_classes_inherit_from_s3boto3(self):
        """Test that storage classes inherit from S3Boto3Storage."""
        from oxutils.s3.storages import (
            StaticStorage,
            PublicMediaStorage,
            PrivateMediaStorage,
            LogStorage,
            S3Boto3Storage
        )
        
        assert issubclass(StaticStorage, S3Boto3Storage)
        assert issubclass(PublicMediaStorage, S3Boto3Storage)
        assert issubclass(PrivateMediaStorage, S3Boto3Storage)
        assert issubclass(LogStorage, S3Boto3Storage)
