"""
Tests for oxutils.auth.emails module.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch


class TestEmailAddressSchema:
    """Tests for EmailAddressSchema."""

    def test_is_model_schema(self):
        from oxutils.auth.emails.schemas import EmailAddressSchema
        from ninja import ModelSchema
        from allauth.account.models import EmailAddress

        assert issubclass(EmailAddressSchema, ModelSchema)
        assert EmailAddressSchema.Meta.model is EmailAddress


class TestStatusEmailAddressSchema:
    """Tests for StatusEmailAddressSchema."""

    def test_has_required_fields(self):
        from oxutils.auth.emails.schemas import StatusEmailAddressSchema

        assert "can_add" in StatusEmailAddressSchema.model_fields
        assert "emails" in StatusEmailAddressSchema.model_fields


class TestAddEmailSchema:
    """Tests for AddEmailSchema."""

    def test_has_email_field(self):
        # AddEmailSchema uses EmailStr with adapter validation that hits DB
        # Just verify the schema class exists and has the right field
        from oxutils.auth.emails.schemas import AddEmailSchema

        assert "email" in AddEmailSchema.model_fields


class TestUserEmailService:
    """Tests for UserEmailService."""

    def test_get_user_emails(self):
        from oxutils.auth.emails.services import UserEmailService

        service = UserEmailService()
        request = Mock()
        request.user = Mock()

        with patch("oxutils.auth.emails.services.EmailAddress") as mock_ea:
            mock_qs = mock_ea.objects.filter.return_value
            mock_qs.order_by.return_value = ["email1", "email2"]
            result = service.get_user_emails(request)
            assert result == ["email1", "email2"]

    def test_can_add_email(self):
        from oxutils.auth.emails.services import UserEmailService

        service = UserEmailService()
        request = Mock()

        with patch("oxutils.auth.emails.services.EmailAddress") as mock_ea:
            mock_ea.objects.can_add_email.return_value = True
            result = service.can_add_email(request)
            assert result is True

    @patch("oxutils.auth.emails.services.flows")
    def test_add_email(self, mock_flows):
        from oxutils.auth.emails.services import UserEmailService

        service = UserEmailService()
        request = Mock()
        form = Mock()

        service.add_email(request, form)
        mock_flows.manage_email.add_email.assert_called_once_with(request, form)

    @patch("oxutils.auth.emails.services.flows")
    def test_set_primary(self, mock_flows):
        from oxutils.auth.emails.services import UserEmailService

        service = UserEmailService()
        request = Mock()
        email_address = Mock()

        mock_flows.manage_email.mark_as_primary.return_value = True
        result = service.set_primary(request, email_address)
        assert result is True

    @patch("oxutils.auth.emails.services.flows")
    def test_remove_email(self, mock_flows):
        from oxutils.auth.emails.services import UserEmailService

        service = UserEmailService()
        request = Mock()

        mock_flows.manage_email.delete_email.return_value = True
        with patch.object(service, "_get_email_address") as mock_get:
            mock_get.return_value = Mock()
            result = service.remove(request, "test@example.com")
            assert result is True

    @patch("oxutils.auth.emails.services.flows")
    def test_sync_user_email_address(self, mock_flows):
        from oxutils.auth.emails.services import UserEmailService

        service = UserEmailService()
        request = Mock()

        service.sync_user_email_address(request)
        mock_flows.manage_email.sync_user_email_address.assert_called_once()

    def test_get_email_address_not_found(self):
        from oxutils.auth.emails.services import UserEmailService

        service = UserEmailService()
        request = Mock()
        request.user = Mock()

        with patch("oxutils.auth.emails.services.EmailAddress") as mock_ea:
            mock_ea.DoesNotExist = type("DoesNotExist", (Exception,), {})
            mock_ea.objects.get_for_user.side_effect = mock_ea.DoesNotExist()
            with patch("oxutils.auth.emails.services.validate_email"):
                result = service._get_email_address(request, "test@example.com")
                assert result is None


class TestEmailThrottleClasses:
    """Tests for email throttle classes."""

    def test_email_add_throttle(self):
        from oxutils.auth.emails.controllers import EmailAddThrottle

        throttle = EmailAddThrottle()
        assert throttle.scope == "email_add"
        assert throttle.rate == "5/hour"

    def test_email_verification_throttle(self):
        from oxutils.auth.emails.controllers import EmailVerificationThrottle

        throttle = EmailVerificationThrottle()
        assert throttle.scope == "email_verification"
        assert throttle.rate == "10/hour"

    def test_email_modification_throttle(self):
        from oxutils.auth.emails.controllers import EmailModificationThrottle

        throttle = EmailModificationThrottle()
        assert throttle.scope == "email_modification"
        assert throttle.rate == "20/hour"
