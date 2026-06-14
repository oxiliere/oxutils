"""
Tests for oxutils.auth.registration module.
"""

from unittest.mock import Mock, patch

import pytest


class TestRegisterSchema:
    """Tests for RegisterSchema."""

    def test_schema_fields(self):
        from oxutils.auth.registration.schemas import RegisterSchema

        schema = RegisterSchema(
            email="test@example.com",
            password1="StrongPass1!",
            password2="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )
        assert schema.email == "test@example.com"
        assert schema.first_name == "John"
        assert schema.last_name == "Doe"

    def test_validate_first_name_capitalizes(self):
        from oxutils.auth.registration.schemas import RegisterSchema

        schema = RegisterSchema(
            email="test@example.com",
            password1="StrongPass1!",
            password2="StrongPass1!",
            first_name="john",
            last_name="doe",
        )
        assert schema.first_name == "John"
        assert schema.last_name == "Doe"

    def test_validate_first_name_compound(self):
        from oxutils.auth.registration.schemas import RegisterSchema

        schema = RegisterSchema(
            email="test@example.com",
            password1="StrongPass1!",
            password2="StrongPass1!",
            first_name="jean pierre",
            last_name="doe",
        )
        assert schema.first_name == "Jean Pierre"

    def test_validate_first_name_rejects_non_letters(self):
        from oxutils.auth.registration.schemas import RegisterSchema

        with pytest.raises(ValueError, match="Incorrect name"):
            RegisterSchema(
                email="test@example.com",
                password1="StrongPass1!",
                password2="StrongPass1!",
                first_name="John123",
                last_name="Doe",
            )

    def test_validate_last_name_rejects_numbers(self):
        from oxutils.auth.registration.schemas import RegisterSchema

        with pytest.raises(ValueError, match="Incorrect name"):
            RegisterSchema(
                email="test@example.com",
                password1="StrongPass1!",
                password2="StrongPass1!",
                first_name="John",
                last_name="Doe456",
            )

    def test_validate_passwords_mismatch(self):
        from oxutils.auth.registration.schemas import RegisterSchema

        with pytest.raises(ValueError, match="didn't match"):
            RegisterSchema(
                email="test@example.com",
                password1="StrongPass1!",
                password2="DifferentPass!",
                first_name="John",
                last_name="Doe",
            )

    def test_token_is_optional(self):
        from oxutils.auth.registration.schemas import RegisterSchema

        schema = RegisterSchema(
            email="test@example.com",
            password1="StrongPass1!",
            password2="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )
        assert schema.token is None

    def test_token_can_be_set(self):
        from oxutils.auth.registration.schemas import RegisterSchema

        schema = RegisterSchema(
            email="test@example.com",
            password1="StrongPass1!",
            password2="StrongPass1!",
            first_name="John",
            last_name="Doe",
            token="invite-token-123",
        )
        assert schema.token == "invite-token-123"

    @patch("oxutils.auth.registration.schemas.get_adapter")
    def test_validate_email_with_token_skips_strict_validation(self, mock_get_adapter):
        from oxutils.auth.registration.schemas import RegisterSchema

        adapter = Mock()
        adapter.clean_email.return_value = "invited@example.com"
        adapter.clean_password.side_effect = lambda p: p  # passthrough
        mock_get_adapter.return_value = adapter

        schema = RegisterSchema(
            email="  invited@example.com  ",
            password1="StrongPass1!",
            password2="StrongPass1!",
            first_name="John",
            last_name="Doe",
            token="invite-token-123",
        )
        assert schema.email == "invited@example.com"

    def test_get_cleaned_data(self):
        from oxutils.auth.registration.schemas import RegisterSchema

        schema = RegisterSchema(
            email="test@example.com",
            password1="StrongPass1!",
            password2="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )
        data = schema.get_cleaned_data()
        assert data["email"] == "test@example.com"
        assert data["password1"] == "StrongPass1!"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"


class TestRegisterResponseSchema:
    """Tests for RegisterResponseSchema."""

    def test_defaults(self):
        from oxutils.auth.registration.schemas import RegisterResponseSchema

        schema = RegisterResponseSchema(success=True, message="OK")
        assert schema.success is True
        assert schema.email_verification_required is False


class TestVerifyEmailSchema:
    """Tests for VerifyEmailSchema."""

    def test_has_key_field(self):
        from oxutils.auth.registration.schemas import VerifyEmailSchema

        schema = VerifyEmailSchema(key="confirmation-key-123")
        assert schema.key == "confirmation-key-123"
