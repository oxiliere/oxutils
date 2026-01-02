from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict




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
    service_name: Optional[str] = 'Oxutils'
    site_name: Optional[str] = 'Oxiliere'
    site_domain: Optional[str] = 'oxiliere.com'
    multitenancy: bool = Field(False)

    # Auth JWT Settings (JWT_SIGNING_KEY)
    jwt_signing_key: Optional[str] = None
    jwt_verifying_key: Optional[str] = None
    jwt_jwks_url: Optional[str] = None
    jwt_access_token_key: str = Field('access')
    jwt_org_access_token_key: str = Field('org_access')
    jwt_service_token_key: str = Field('service')
    jwt_algorithm: Optional[str] = Field('RS256')
    jwt_access_token_lifetime: int = Field(15) # minutes
    jwt_service_token_lifetime: int = Field(3) # minutes
    jwt_org_access_token_lifetime: int = Field(60) # minutes


    # AuditLog
    log_access: bool = Field(False)
    retention_delay: int = Field(7)  # one week

    # logger
    log_file_path: Optional[str] = Field('logs/oxiliere.log')

    def model_post_init(self, __context):
        """Called after model initialization to perform validation."""
        self._validate_jwt_keys()
    
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
                

oxi_settings = OxUtilsSettings()
