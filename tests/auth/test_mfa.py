"""
Tests for oxutils.auth.mfa module.
"""

from unittest.mock import patch

import pytest


class TestMFAUtils:
    """Tests for oxutils.auth.mfa.utils."""

    @patch("oxutils.auth.mfa.utils.settings")
    def test_get_mfa_signing_salt_from_settings(self, mock_settings):
        from oxutils.auth.mfa.utils import get_mfa_signing_salt

        mock_settings.MFA_SIGNING_SALT = "custom-salt"
        result = get_mfa_signing_salt()
        assert result == "custom-salt"

    def test_get_mfa_signing_salt_default_value(self):
        from oxutils.auth.mfa.utils import get_mfa_signing_salt

        with patch("oxutils.auth.mfa.utils.settings") as mock_settings:
            mock_settings.DEBUG = True
            del mock_settings.MFA_SIGNING_SALT
            result = get_mfa_signing_salt()
            assert result == "mfa-login-required-dev-only"

    @patch("oxutils.auth.mfa.utils.settings")
    def test_get_mfa_signing_ttl(self, mock_settings):
        from oxutils.auth.mfa.utils import get_mfa_signing_ttl

        mock_settings.MFA_SIGNING_TTL = 600
        result = get_mfa_signing_ttl()
        assert result == 600


class TestMFAAdapter:
    """Tests for MFAAdapter."""

    def test_is_subclass_of_default(self):
        from oxutils.auth.mfa.adapter import MFAAdapter

        assert MFAAdapter is not None

    def test_can_instantiate(self):
        from oxutils.auth.mfa.adapter import MFAAdapter

        adapter = MFAAdapter()
        assert adapter is not None


class TestTOTPSchemas:
    """Tests for TOTP schemas."""

    def test_activate_totp_code_validation(self):
        from oxutils.auth.mfa.totp.schemas import ActivateTOTPSchema

        schema = ActivateTOTPSchema(code="123456", secret="mysecret")
        assert schema.code == "123456"
        assert schema.secret == "mysecret"

    def test_activate_totp_code_non_digit_raises(self):
        from oxutils.auth.mfa.totp.schemas import ActivateTOTPSchema

        with pytest.raises(ValueError, match="digits"):
            ActivateTOTPSchema(code="abcdef", secret="mysecret")

    def test_totp_secret_request_schema(self):
        from oxutils.auth.mfa.totp.schemas import TOTPSecretRequestSchema

        schema = TOTPSecretRequestSchema()
        assert schema.regenerate is False

    def test_totp_secret_request_regenerate(self):
        from oxutils.auth.mfa.totp.schemas import TOTPSecretRequestSchema

        schema = TOTPSecretRequestSchema(regenerate=True)
        assert schema.regenerate is True

    def test_totp_secret_response_schema(self):
        from oxutils.auth.mfa.totp.schemas import TOTPSecretResponseSchema

        schema = TOTPSecretResponseSchema(
            secret="secret", qr_code_url="data:image/svg+xml;base64,abc"
        )
        assert schema.secret == "secret"
        assert schema.qr_code_url == "data:image/svg+xml;base64,abc"

    def test_totp_activation_response_schema(self):
        from oxutils.auth.mfa.totp.schemas import TOTPActivationResponseSchema

        schema = TOTPActivationResponseSchema(success=True, message="OK")
        assert schema.success is True
        assert schema.message == "OK"

    def test_totp_deactivation_response_schema(self):
        from oxutils.auth.mfa.totp.schemas import TOTPDeactivationResponseSchema

        schema = TOTPDeactivationResponseSchema(success=True, message="Deactivated")
        assert schema.success is True

    def test_totp_status_response_schema(self):
        from oxutils.auth.mfa.totp.schemas import TOTPStatusResponseSchema

        schema = TOTPStatusResponseSchema(is_active=False)
        assert schema.is_active is False
        assert schema.created_at is None
        assert schema.last_used_at is None


class TestRecoveryCodesSchemas:
    """Tests for recovery codes schemas."""

    def test_generate_schema(self):
        from oxutils.auth.mfa.recovery_codes.schemas import RecoveryCodesGenerateSchema

        schema = RecoveryCodesGenerateSchema()
        assert schema is not None

    def test_status_response_schema(self):
        from oxutils.auth.mfa.recovery_codes.schemas import (
            RecoveryCodesStatusResponseSchema,
        )

        schema = RecoveryCodesStatusResponseSchema(
            is_active=True, unused_codes=["code1", "code2"], total_count=10
        )
        assert schema.is_active is True
        assert schema.unused_codes == ["code1", "code2"]
        assert schema.total_count == 10

    def test_generate_response_schema(self):
        from oxutils.auth.mfa.recovery_codes.schemas import (
            RecoveryCodesGenerateResponseSchema,
        )

        schema = RecoveryCodesGenerateResponseSchema(
            success=True, message="Done", codes=["c1", "c2"]
        )
        assert schema.success is True
        assert schema.codes == ["c1", "c2"]

    def test_download_response_schema(self):
        from oxutils.auth.mfa.recovery_codes.schemas import (
            RecoveryCodesDownloadResponseSchema,
        )

        schema = RecoveryCodesDownloadResponseSchema(
            content="content", filename="file.txt", content_type="text/plain"
        )
        assert schema.content == "content"
        assert schema.filename == "file.txt"
        assert schema.content_type == "text/plain"
