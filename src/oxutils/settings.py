import base64
import binascii
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

    # Auth JWT Settings — base64-encoded PEM strings
    jwt_signing_key: Optional[str] = None
    jwt_verifying_key: Optional[str] = None
    jwt_jwks_url: Optional[str] = None
    jwt_access_token_key: str = Field('access')
    jwt_algorithm: Optional[str] = Field('RS256')
    jwt_access_token_lifetime: int = Field(15)  # minutes

    # AuditLog
    log_access: bool = Field(False)
    retention_delay: int = Field(7)  # one week

    # logger
    log_file_path: Optional[str] = Field('logs/oxiliere.log')

    def model_post_init(self, __context):
        """Called after model initialization to perform validation."""
        self._validate_jwt_keys()

    @staticmethod
    def _decode_jwt_key(value: str, name: str) -> str:
        """Decode a base64-encoded PEM key, raising ValueError if invalid."""
        try:
            decoded = base64.b64decode("".join(value.split()), validate=True)
            return decoded.decode("utf-8")
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise ValueError(
                f"{name} is not a valid base64-encoded PEM string: {exc}"
            ) from exc

    def _validate_jwt_keys(self):
        """Validate that configured JWT keys are valid base64-encoded PEM strings."""
        if self.jwt_signing_key:
            self._decode_jwt_key(self.jwt_signing_key, "JWT signing key")

        if self.jwt_verifying_key:
            self._decode_jwt_key(self.jwt_verifying_key, "JWT verifying key")

    @property
    def jwt_signing_key_pem(self) -> Optional[str]:
        """The decoded PEM signing key, or None if not configured."""
        if not self.jwt_signing_key:
            return None
        return self._decode_jwt_key(self.jwt_signing_key, "JWT signing key")

    @property
    def jwt_verifying_key_pem(self) -> Optional[str]:
        """The decoded PEM verifying key, or None if not configured."""
        if not self.jwt_verifying_key:
            return None
        return self._decode_jwt_key(self.jwt_verifying_key, "JWT verifying key")


oxi_settings = OxUtilsSettings()
