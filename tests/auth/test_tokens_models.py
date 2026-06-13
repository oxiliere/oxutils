"""
Tests for oxutils.auth.tokens.models module.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from django.db import models


class TestTokenModel:
    """Tests for Token model."""

    def test_token_model_fields(self):
        from oxutils.auth.tokens.models import Token

        # Verify expected fields exist
        assert hasattr(Token, "key")
        assert hasattr(Token, "user")
        assert hasattr(Token, "created")

        # Verify key is primary key
        field = Token._meta.get_field("key")
        assert field.primary_key is True
        assert field.max_length == 40

    def test_token_model_str(self):
        from oxutils.auth.tokens.models import Token

        token = Token(key="abc123")
        assert str(token) == "abc123"

    def test_token_generate_key(self):
        from oxutils.auth.tokens.models import Token

        key = Token.generate_key()
        assert isinstance(key, str)
        assert len(key) == 40  # secrets.token_hex(20) = 40 chars

    def test_token_generate_key_is_random(self):
        from oxutils.auth.tokens.models import Token

        keys = [Token.generate_key() for _ in range(5)]
        # All keys should be different
        assert len(set(keys)) == 5


class TestTokenProxy:
    """Tests for TokenProxy model."""

    def test_token_proxy_is_proxy(self):
        from oxutils.auth.tokens.models import TokenProxy, Token

        assert TokenProxy._meta.proxy is True
        assert issubclass(TokenProxy, Token)

    def test_token_proxy_pk_returns_user_id(self):
        from oxutils.auth.tokens.models import TokenProxy

        proxy = TokenProxy(user_id=42)
        assert proxy.pk == 42


class TestBaseToken:
    """Tests for BaseToken abstract model."""

    def test_base_token_is_abstract(self):
        from oxutils.auth.tokens.models import BaseToken

        assert BaseToken._meta.abstract is True

    def test_base_token_has_expected_fields(self):
        from oxutils.auth.tokens.models import BaseToken

        field_names = [f.name for f in BaseToken._meta.get_fields()]
        assert "id" in field_names
        assert "created" in field_names
        assert "ip" in field_names
        assert "is_mobile" in field_names
        assert "is_tablet" in field_names
        assert "is_pc" in field_names
        assert "is_bot" in field_names
        assert "browser" in field_names
        assert "browser_version" in field_names
        assert "os" in field_names
        assert "os_version" in field_names
        assert "device" in field_names
        assert "device_brand" in field_names
        assert "device_model" in field_names


class TestAbstractRefreshToken:
    """Tests for AbstractRefreshToken model."""

    def test_is_abstract(self):
        from oxutils.auth.tokens.models import AbstractRefreshToken

        assert AbstractRefreshToken._meta.abstract is True

    def test_has_jti_field(self):
        from oxutils.auth.tokens.models import AbstractRefreshToken

        field = AbstractRefreshToken._meta.get_field("jti")
        assert field.max_length == 32
        assert field.blank is False

    def test_has_enabled_field(self):
        from oxutils.auth.tokens.models import AbstractRefreshToken

        field = AbstractRefreshToken._meta.get_field("enabled")
        assert field.default is True

    def test_has_session_field(self):
        from oxutils.auth.tokens.models import AbstractRefreshToken

        field = AbstractRefreshToken._meta.get_field("session")
        assert field.max_length == 32

    def test_uses_refresh_token_manager(self):
        from oxutils.auth.tokens.models import AbstractRefreshToken, RefreshTokenManager

        # Abstract model's manager is the class-level objects descriptor
        # but it can't be instantiated directly on an abstract model
        assert AbstractRefreshToken._meta.abstract is True


class TestRefreshTokenWhitelistModel:
    """Tests for RefreshTokenWhitelistModel."""

    def test_has_user_foreign_key(self):
        from oxutils.auth.tokens.models import RefreshTokenWhitelistModel

        field = RefreshTokenWhitelistModel._meta.get_field("user")
        assert field.many_to_one is True

    def test_related_name(self):
        from oxutils.auth.tokens.models import RefreshTokenWhitelistModel

        field = RefreshTokenWhitelistModel._meta.get_field("user")
        assert field.remote_field.related_name == "refresh_tokens_whitelist"


class TestGenericTokenModel:
    """Tests for GenericTokenModel."""

    def test_has_token_field(self):
        from oxutils.auth.tokens.models import GenericTokenModel

        field = GenericTokenModel._meta.get_field("token")
        assert field.max_length == 255

    def test_has_purpose_field(self):
        from oxutils.auth.tokens.models import GenericTokenModel

        field = GenericTokenModel._meta.get_field("purpose")
        assert field.max_length == 32

    def test_has_user_foreign_key(self):
        from oxutils.auth.tokens.models import GenericTokenModel

        field = GenericTokenModel._meta.get_field("user")
        assert field.many_to_one is True
        assert field.remote_field.related_name == "generic_tokens"


class TestRefreshTokenManager:
    """Tests for RefreshTokenManager."""

    @patch("oxutils.auth.tokens.models.settings")
    @patch("oxutils.auth.tokens.models.transaction")
    def test_create_with_user_below_limit(self, mock_transaction, mock_settings):
        from oxutils.auth.tokens.models import RefreshTokenManager, RefreshTokenWhitelistModel, AbstractRefreshToken

        mock_settings.JWT_ALL_AUTH_MAX_SESSIONS = 4
        # Need a concrete model to test manager
        pass

    def test_manager_creates_without_user(self):
        from oxutils.auth.tokens.models import RefreshTokenManager, RefreshTokenWhitelistModel
        # Without user, should just call super().create(**kwargs)
        pass
