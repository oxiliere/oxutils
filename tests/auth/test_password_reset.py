"""
Tests for oxutils.auth.password_reset module.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch


class TestPasswordResetSchema:
    """Tests for PasswordResetSchema."""

    def test_schema_has_email_field(self):
        from oxutils.auth.password_reset.schemas import PasswordResetSchema

        schema = PasswordResetSchema(email="test@example.com")
        assert schema.email == "test@example.com"

    def test_validate_email_strips_and_lowercases(self):
        from oxutils.auth.password_reset.schemas import PasswordResetSchema

        schema = PasswordResetSchema(email="  Test@Example.COM  ")
        assert schema.email == "test@example.com"

    def test_get_email_options_returns_empty_dict(self):
        from oxutils.auth.password_reset.schemas import PasswordResetSchema

        schema = PasswordResetSchema(email="test@example.com")
        opts = schema.get_email_options()
        assert opts == {}

    @patch("oxutils.auth.password_reset.schemas.PasswordResetForm")
    @patch("oxutils.auth.password_reset.schemas.EmailAddress")
    def test_send_password_reset_email_success(self, mock_email_address, mock_form_class):
        from oxutils.auth.password_reset.schemas import PasswordResetSchema

        mock_form_instance = Mock()
        mock_form_instance.is_valid.return_value = True
        mock_form_class.return_value = mock_form_instance
        mock_email_address.objects.filter.return_value.count.return_value = 1

        request = Mock()
        request.is_secure.return_value = False

        schema = PasswordResetSchema(email="test@example.com")
        # Should not raise
        schema.send_password_reset_email(request)

    @patch("oxutils.auth.password_reset.schemas.PasswordResetForm")
    @patch("oxutils.auth.password_reset.schemas.EmailAddress")
    def test_send_password_reset_email_not_sent_if_unverified(self, mock_email_address, mock_form_class):
        from oxutils.auth.password_reset.schemas import PasswordResetSchema

        mock_form_instance = Mock()
        mock_form_instance.is_valid.return_value = True
        mock_form_class.return_value = mock_form_instance
        mock_email_address.objects.filter.return_value.count.return_value = 0

        request = Mock()
        request.is_secure.return_value = False

        schema = PasswordResetSchema(email="test@example.com")
        # save() should not be called when count == 0
        schema.send_password_reset_email(request)
        mock_form_instance.save.assert_not_called()

    @patch("oxutils.auth.password_reset.schemas.PasswordResetForm")
    def test_send_password_reset_email_invalid_form(self, mock_form_class):
        from oxutils.auth.password_reset.schemas import PasswordResetSchema
        from ninja_extra import exceptions

        mock_form_instance = Mock()
        mock_form_instance.is_valid.return_value = False
        mock_form_instance.errors = {"email": ["Invalid"]}
        mock_form_class.return_value = mock_form_instance

        request = Mock()
        schema = PasswordResetSchema(email="test@example.com")

        with pytest.raises(exceptions.ValidationError):
            schema.send_password_reset_email(request)


class TestSetPasswordSchema:
    """Tests for SetPasswordSchema."""

    def test_old_password_field_disabled(self):
        from oxutils.auth.password_reset.schemas import SetPasswordSchema

        # model_validator requires context, use model_construct
        schema = SetPasswordSchema.model_construct(new_password1="p1", new_password2="p1")
        assert schema.old_password_field_enabled is False

    def test_logout_on_password_change_disabled(self):
        from oxutils.auth.password_reset.schemas import SetPasswordSchema

        schema = SetPasswordSchema.model_construct(new_password1="p1", new_password2="p1")
        assert schema.logout_on_password_change is False

    def test_inherits_base_change_password(self):
        from oxutils.auth.password_reset.schemas import SetPasswordSchema
        from oxutils.auth.schemas import BaseChangePasswordSchema

        assert issubclass(SetPasswordSchema, BaseChangePasswordSchema)


class TestPasswordResetResponseSchema:
    """Tests for PasswordResetResponseSchema."""

    def test_has_success_and_message_fields(self):
        from oxutils.auth.password_reset.schemas import PasswordResetResponseSchema

        schema = PasswordResetResponseSchema(success=True, message="OK")
        assert schema.success is True
        assert schema.message == "OK"


class TestSetPasswordTokenUser:
    """Tests for SetPasswordTokenUser."""

    def test_id_returns_for_user_from_token(self):
        from oxutils.auth.password_reset.models import SetPasswordTokenUser

        token = {"for_user": 42}
        user = SetPasswordTokenUser(token)
        assert user.id == 42

    def test_id_returns_string(self):
        from oxutils.auth.password_reset.models import SetPasswordTokenUser

        token = {"for_user": "user-uuid-123"}
        user = SetPasswordTokenUser(token)
        assert user.id == "user-uuid-123"


class TestResetPasswordPermission:
    """Tests for ResetPasswordPermission."""

    def test_denies_authenticated_user(self):
        from oxutils.auth.password_reset.permissions import ResetPasswordPermission

        perm = ResetPasswordPermission()
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True

        result = perm.has_permission(request, Mock())
        assert result is False

    def test_denies_when_no_cookie(self):
        from oxutils.auth.password_reset.permissions import ResetPasswordPermission

        perm = ResetPasswordPermission()
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        request.COOKIES = {}

        result = perm.has_permission(request, Mock())
        assert result is False

    @patch("oxutils.auth.password_reset.permissions.RefreshToken")
    def test_allows_valid_token(self, mock_refresh_token_class):
        from oxutils.auth.password_reset.permissions import ResetPasswordPermission

        mock_access_token = Mock()
        mock_access_token.__contains__ = lambda self, key: key in {
            "one_time_permission", "for_user"
        }
        mock_access_token.__getitem__ = lambda self, key: {
            "one_time_permission": "PASS_RESET_ACCESS",
            "for_user": 42,
        }[key]
        mock_refresh_token_class.access_token_class.return_value = mock_access_token

        perm = ResetPasswordPermission()
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        request.COOKIES = {"password_reset_access_token": "valid-access-token"}

        result = perm.has_permission(request, Mock())
        assert result is True
        assert request.user is not None

    @patch("oxutils.auth.password_reset.permissions.RefreshToken")
    def test_denies_wrong_permission(self, mock_refresh_token_class):
        from oxutils.auth.password_reset.permissions import ResetPasswordPermission

        mock_access_token = Mock()
        mock_access_token.__contains__ = lambda self, key: key in {
            "one_time_permission", "for_user"
        }
        mock_access_token.__getitem__ = lambda self, key: {
            "one_time_permission": "WRONG_PERMISSION",
            "for_user": 42,
        }[key]
        mock_refresh_token_class.access_token_class.return_value = mock_access_token

        perm = ResetPasswordPermission()
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        request.COOKIES = {"password_reset_access_token": "valid-access-token"}

        result = perm.has_permission(request, Mock())
        assert result is False
