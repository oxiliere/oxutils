"""
Tests for JWT JWKS generation from base64-encoded keys.
"""

import pytest
from django.core.exceptions import ImproperlyConfigured

from oxutils.jwt.auth import clear_jwk_cache, get_jwks
from oxutils.settings import oxi_settings


@pytest.fixture(autouse=True)
def restore_verifying_key():
    """Restore the global verifying key and reset the JWK cache."""
    original = oxi_settings.jwt_verifying_key
    clear_jwk_cache()
    yield
    oxi_settings.jwt_verifying_key = original
    clear_jwk_cache()


def test_get_jwks_from_base64_key(temp_jwt_key):
    oxi_settings.jwt_verifying_key = temp_jwt_key["public_key_b64"]

    jwks = get_jwks()

    keys = jwks["keys"]
    assert len(keys) == 1
    assert keys[0]["kid"] == "main"
    assert keys[0]["kty"] == "RSA"


def test_get_jwks_not_configured():
    oxi_settings.jwt_verifying_key = None

    with pytest.raises(ImproperlyConfigured, match="JWT verifying key is not configured"):
        get_jwks()
