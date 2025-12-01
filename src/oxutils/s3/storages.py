from storages.backends.s3boto3 import S3Boto3Storage
from oxutils.settings import oxi_settings
from django.core.exceptions import ImproperlyConfigured


class StaticStorage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        if not oxi_settings.use_static_s3:
            raise ImproperlyConfigured(
                "StaticStorage requires OXI_USE_STATIC_S3=True"
            )
        
        self.access_key = oxi_settings.static_access_key_id
        self.secret_key = oxi_settings.static_secret_access_key
        self.bucket_name = oxi_settings.static_storage_bucket_name
        self.custom_domain = oxi_settings.static_s3_custom_domain
        self.location = oxi_settings.static_location
        self.default_acl = oxi_settings.static_default_acl
        self.file_overwrite = False
        
        self._validate_required_fields('StaticStorage', {
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'bucket_name': self.bucket_name,
            'custom_domain': self.custom_domain,
        })
        
        super().__init__(*args, **kwargs)
    
    @staticmethod
    def _validate_required_fields(storage_name: str, fields: dict):
        """Validate that all required fields are present."""
        missing = [name for name, value in fields.items() if not value]
        if missing:
            raise ImproperlyConfigured(
                f"{storage_name} is missing required configuration: {', '.join(missing)}"
            )


class PublicMediaStorage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        if not oxi_settings.use_default_s3:
            raise ImproperlyConfigured(
                "PublicMediaStorage requires OXI_USE_DEFAULT_S3=True"
            )
        
        if oxi_settings.use_static_s3_as_default:
            self.access_key = oxi_settings.static_access_key_id
            self.secret_key = oxi_settings.static_secret_access_key
            self.bucket_name = oxi_settings.static_storage_bucket_name
            self.custom_domain = oxi_settings.static_s3_custom_domain
        else:
            self.access_key = oxi_settings.default_s3_access_key_id
            self.secret_key = oxi_settings.default_s3_secret_access_key
            self.bucket_name = oxi_settings.default_s3_storage_bucket_name
            self.custom_domain = oxi_settings.default_s3_s3_custom_domain
        
        self.location = oxi_settings.default_s3_location
        self.default_acl = oxi_settings.default_s3_default_acl
        self.file_overwrite = False
        
        StaticStorage._validate_required_fields('PublicMediaStorage', {
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'bucket_name': self.bucket_name,
            'custom_domain': self.custom_domain,
        })
        
        super().__init__(*args, **kwargs)


class PrivateMediaStorage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        if not oxi_settings.use_private_s3:
            raise ImproperlyConfigured(
                "PrivateMediaStorage requires OXI_USE_PRIVATE_S3=True"
            )
        
        self.access_key = oxi_settings.private_s3_access_key_id
        self.secret_key = oxi_settings.private_s3_secret_access_key
        self.bucket_name = oxi_settings.private_s3_storage_bucket_name
        self.custom_domain = oxi_settings.private_s3_s3_custom_domain
        self.location = oxi_settings.private_s3_location
        self.default_acl = oxi_settings.private_s3_default_acl
        self.file_overwrite = False
        self.querystring_auth = True
        self.querystring_expire = 3600
        
        StaticStorage._validate_required_fields('PrivateMediaStorage', {
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'bucket_name': self.bucket_name,
            'custom_domain': self.custom_domain,
        })
        
        super().__init__(*args, **kwargs)


class LogStorage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        if not oxi_settings.use_log_s3:
            raise ImproperlyConfigured(
                "LogStorage requires OXI_USE_LOG_S3=True"
            )
        
        if oxi_settings.use_private_s3_as_log:
            self.access_key = oxi_settings.private_s3_access_key_id
            self.secret_key = oxi_settings.private_s3_secret_access_key
            self.bucket_name = oxi_settings.private_s3_storage_bucket_name
            self.custom_domain = oxi_settings.private_s3_s3_custom_domain
        else:
            self.access_key = oxi_settings.log_s3_access_key_id
            self.secret_key = oxi_settings.log_s3_secret_access_key
            self.bucket_name = oxi_settings.log_s3_storage_bucket_name
            self.custom_domain = oxi_settings.log_s3_s3_custom_domain
        
        self.location = f'{oxi_settings.log_s3_location}/{oxi_settings.service_name}'
        self.default_acl = oxi_settings.log_s3_default_acl
        self.file_overwrite = False
        self.querystring_auth = True
        self.querystring_expire = 3600
        
        StaticStorage._validate_required_fields('LogStorage', {
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'bucket_name': self.bucket_name,
            'custom_domain': self.custom_domain,
        })
        
        super().__init__(*args, **kwargs)
