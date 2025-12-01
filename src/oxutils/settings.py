from typing import Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from django.core.exceptions import ImproperlyConfigured




__all__ = [
    'oxi_settings',
]



class OxUtilsSettings(BaseSettings):
    model_config = SettingsConfigDict(
        validate_assignment=True,
        extra="ignore",
        env_prefix='OXI_'
    )

    # Service
    service_name: str

    # Auth JWT Settings (JWT_SIGNING_KEY)
    jwt_signing_key: Optional[str] = None
    jwt_verifying_key: Optional[str] = None
    jwt_jwks_url: Optional[str] = None
    jwt_access_token_key: str = Field('access_token') 
    jwt_org_access_token_key: str = Field('org_access_token')


    # AuditLog
    log_access: bool = Field(False)
    retention_delay: int = Field(7)  # one week


    # Static S3
    use_static_s3: bool = Field(False)
    static_access_key_id: Optional[str] = None
    static_secret_access_key: Optional[str] = None
    static_storage_bucket_name: Optional[str] = None
    static_default_acl: str = Field('public-read')
    static_s3_custom_domain: Optional[str] = None
    static_location: str = Field('static')
    static_storage: str = Field('oxutils.s3.storages.StaticStorage')

    # Default S3 for media
    use_default_s3: bool = Field(False)
    use_static_s3_as_default: bool = Field(False)
    default_s3_access_key_id: Optional[str] = None
    default_s3_secret_access_key: Optional[str] = None
    default_s3_storage_bucket_name: Optional[str] = None
    default_s3_default_acl: str = Field('public-read')
    default_s3_s3_custom_domain: Optional[str] = None
    default_s3_location: str = Field('media')
    default_s3_storage: str = Field('oxutils.s3.storages.PublicMediaStorage')

    # Private S3 for sensible data
    use_private_s3: bool = Field(False)
    private_s3_access_key_id: Optional[str] = None
    private_s3_secret_access_key: Optional[str] = None
    private_s3_storage_bucket_name: Optional[str] = None
    private_s3_default_acl: str = Field('private')
    private_s3_s3_custom_domain: Optional[str] = None
    private_s3_location: str = Field('private')
    private_s3_storage: str = Field('oxutils.s3.storages.PrivateMediaStorage')

    # Log S3
    use_log_s3: bool = Field(False)
    use_private_s3_as_log: bool = Field(False)
    log_s3_access_key_id: Optional[str] = None
    log_s3_secret_access_key: Optional[str] = None
    log_s3_storage_bucket_name: Optional[str] = None
    log_s3_default_acl: str = Field('private')
    log_s3_s3_custom_domain: Optional[str] = None
    log_s3_location: str = Field('oxi_logs')
    log_s3_storage: str = Field('oxutils.s3.storages.LogStorage')


    @model_validator(mode='after')
    def validate_s3_configurations(self):
        """Validate S3 and JWT configurations when enabled."""
        # Validate JWT keys if present
        self._validate_jwt_keys()
        
        # Validate static S3
        if self.use_static_s3:
            self._validate_s3_config(
                'static',
                self.static_access_key_id,
                self.static_secret_access_key,
                self.static_storage_bucket_name,
                self.static_s3_custom_domain
            )
        
        # Validate default S3
        if self.use_default_s3:
            if not self.use_static_s3_as_default:
                self._validate_s3_config(
                    'default',
                    self.default_s3_access_key_id,
                    self.default_s3_secret_access_key,
                    self.default_s3_storage_bucket_name,
                    self.default_s3_s3_custom_domain
                )
            elif not self.use_static_s3:
                raise ValueError(
                    "OXI_USE_STATIC_S3_AS_DEFAULT requires OXI_USE_STATIC_S3 to be True"
                )
        
        # Validate private S3
        if self.use_private_s3:
            self._validate_s3_config(
                'private',
                self.private_s3_access_key_id,
                self.private_s3_secret_access_key,
                self.private_s3_storage_bucket_name,
                self.private_s3_s3_custom_domain
            )
        
        # Validate log S3
        if self.use_log_s3:
            if not self.use_private_s3_as_log:
                self._validate_s3_config(
                    'log',
                    self.log_s3_access_key_id,
                    self.log_s3_secret_access_key,
                    self.log_s3_storage_bucket_name,
                    self.log_s3_s3_custom_domain
                )
            elif not self.use_private_s3:
                raise ValueError(
                    "OXI_USE_PRIVATE_S3_AS_LOG requires OXI_USE_PRIVATE_S3 to be True"
                )
        
        return self
    
    def _validate_jwt_keys(self):
        """Validate JWT key files if configured."""
        import os
        
        if self.jwt_signing_key:
            if not os.path.exists(self.jwt_signing_key):
                raise ValueError(
                    f"JWT signing key file not found at: {self.jwt_signing_key}"
                )
            if not os.path.isfile(self.jwt_signing_key):
                raise ValueError(
                    f"JWT signing key path is not a file: {self.jwt_signing_key}"
                )
        
        if self.jwt_verifying_key:
            if not os.path.exists(self.jwt_verifying_key):
                raise ValueError(
                    f"JWT verifying key file not found at: {self.jwt_verifying_key}"
                )
            if not os.path.isfile(self.jwt_verifying_key):
                raise ValueError(
                    f"JWT verifying key path is not a file: {self.jwt_verifying_key}"
                )
    
    def _validate_s3_config(self, name: str, access_key: Optional[str], 
                           secret_key: Optional[str], bucket: Optional[str], 
                           domain: Optional[str]):
        """Validate required S3 configuration fields."""
        missing_fields = []
        if not access_key:
            missing_fields.append(f'OXI_{name.upper()}_ACCESS_KEY_ID')
        if not secret_key:
            missing_fields.append(f'OXI_{name.upper()}_SECRET_ACCESS_KEY')
        if not bucket:
            missing_fields.append(f'OXI_{name.upper()}_STORAGE_BUCKET_NAME')
        if not domain:
            missing_fields.append(f'OXI_{name.upper()}_S3_CUSTOM_DOMAIN')
        
        if missing_fields:
            raise ValueError(
                f"Missing required {name} S3 configuration: {', '.join(missing_fields)}"
            )

    def get_static_storage_url(self) -> str:
        """Get static storage URL."""
        if not self.use_static_s3:
            raise ImproperlyConfigured(
                "Static S3 is not enabled. Set OXI_USE_STATIC_S3=True."
            )
        return f'https://{self.static_s3_custom_domain}/{self.static_location}/'

    def get_default_storage_url(self) -> str:
        """Get default storage URL."""
        if self.use_default_s3:
            if self.use_static_s3_as_default:
                # Use static S3 credentials but keep default_s3 specific values (location, etc.)
                domain = self.static_s3_custom_domain
            else:
                domain = self.default_s3_s3_custom_domain
            return f'https://{domain}/{self.default_s3_location}/'
        
        raise ImproperlyConfigured(
            "Default S3 is not enabled. Set OXI_USE_DEFAULT_S3=True."
        )
    
    def get_private_storage_url(self) -> str:
        """Get private storage URL."""
        if not self.use_private_s3:
            raise ImproperlyConfigured(
                "Private S3 is not enabled. Set OXI_USE_PRIVATE_S3=True."
            )
        return f'https://{self.private_s3_s3_custom_domain}/{self.private_s3_location}/'
    
    def get_log_storage_url(self) -> str:
        """Get log storage URL."""
        if not self.use_log_s3:
            raise ImproperlyConfigured(
                "Log S3 is not enabled. Set OXI_USE_LOG_S3=True."
            )
        if self.use_private_s3_as_log:
            # Use private S3 credentials but keep log_s3 specific values (location, etc.)
            domain = self.private_s3_s3_custom_domain
        else:
            domain = self.log_s3_s3_custom_domain
        return f'https://{domain}/{self.log_s3_location}/{self.service_name}/'


    def write_django_settings(self, django_settings_module):
        """
        Configure Django settings for S3 storages if enabled.
        
        Sets:
        1. STATIC_URL & STATICFILES_STORAGE (if use_static_s3)
        2. MEDIA_URL & DEFAULT_FILE_STORAGE (if use_default_s3)
        3. PRIVATE_MEDIA_LOCATION & PRIVATE_FILE_STORAGE (if use_private_s3)
        
        Args:
            django_settings_module: The Django settings module to update.
        """
        # Configure static storage
        if self.use_static_s3:
            django_settings_module.STATIC_URL = self.get_static_storage_url()
            django_settings_module.STATICFILES_STORAGE = self.static_storage
        
        # Configure default/media storage
        if self.use_default_s3:
            django_settings_module.MEDIA_URL = self.get_default_storage_url()
            django_settings_module.DEFAULT_FILE_STORAGE = self.default_s3_storage
        
        # Configure private storage
        if self.use_private_s3:
            django_settings_module.PRIVATE_MEDIA_LOCATION = self.private_s3_location
            django_settings_module.PRIVATE_FILE_STORAGE = self.private_s3_storage


oxi_settings = OxUtilsSettings()
