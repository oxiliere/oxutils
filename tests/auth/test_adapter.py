"""
Tests for oxutils.auth.adapter module.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from oxutils.auth.adapter import JWTAllAuthAdapter


class TestJWTAllAuthAdapter:
    """Tests for JWTAllAuthAdapter."""

    def setup_method(self):
        self.adapter = JWTAllAuthAdapter()

    def test_clean_email_normalizes(self, mock_email_address, mock_allauth_app_settings):
        mock_email_address.filter.return_value.exists.return_value = False
        result = self.adapter.clean_email("  Test@Example.Com  ")
        assert result == "test@example.com"

    def test_clean_email_raises_for_duplicate_verified(
        self, mock_email_address, mock_allauth_app_settings
    ):
        mock_email_address.filter.return_value.exists.return_value = True
        with pytest.raises(ValueError, match="already registered"):
            self.adapter.clean_email("test@example.com")

    def test_clean_email_deletes_non_verified_duplicates(
        self, mock_email_address, mock_allauth_app_settings
    ):
        mock_email_address.filter.return_value.exists.return_value = False
        result = self.adapter.clean_email("test@example.com")
        assert result == "test@example.com"
        mock_email_address.filter.assert_any_call(email="test@example.com", verified=False)

    def test_populate_username_does_nothing(self):
        self.adapter.populate_username(Mock(), Mock())

    @patch("oxutils.auth.adapter.format_confirm_email_url")
    def test_get_email_confirmation_url(self, mock_format):
        mock_format.return_value = "https://app.example.com/confirm/abc123"
        email_confirmation = Mock(key="abc123")
        url = self.adapter.get_email_confirmation_url(Mock(), email_confirmation)
        assert url == "https://app.example.com/confirm/abc123"

    @patch.object(JWTAllAuthAdapter, "send_mail")
    @patch.object(JWTAllAuthAdapter, "get_email_confirmation_url")
    @patch("oxutils.auth.adapter.get_template_path")
    def test_send_confirmation_mail_signup(
        self, mock_get_template_path, mock_get_url, mock_send_mail, mock_allauth_app_settings
    ):
        mock_allauth_app_settings.EMAIL_VERIFICATION_BY_CODE_ENABLED = False
        mock_get_url.return_value = "https://example.com/confirm/key123"
        mock_get_template_path.return_value = "custom/template.html"
        email_confirmation = Mock()
        email_confirmation.key = "key123"
        email_confirmation.email_address.email = "test@example.com"
        email_confirmation.email_address.user = Mock()
        result = self.adapter.send_confirmation_mail(Mock(), email_confirmation, signup=True)
        assert result == "key123"
        assert mock_send_mail.called

    @patch.object(JWTAllAuthAdapter, "send_mail")
    @patch("oxutils.auth.adapter.get_template_path")
    def test_send_confirmation_mail_not_signup(
        self, mock_get_template_path, mock_send_mail, mock_allauth_app_settings
    ):
        mock_allauth_app_settings.EMAIL_VERIFICATION_BY_CODE_ENABLED = False
        email_confirmation = Mock()
        email_confirmation.key = "key456"
        email_confirmation.email_address.email = "test@example.com"
        email_confirmation.email_address.user = Mock()
        result = self.adapter.send_confirmation_mail(Mock(), email_confirmation, signup=False)
        assert result == "key456"
        assert mock_send_mail.called

    @patch.object(JWTAllAuthAdapter, "send_mail")
    @patch("oxutils.auth.adapter.get_template_path")
    def test_send_confirmation_mail_by_code(
        self, mock_get_template_path, mock_send_mail, mock_allauth_app_settings
    ):
        mock_allauth_app_settings.EMAIL_VERIFICATION_BY_CODE_ENABLED = False
        mock_get_template_path.return_value = "custom/template.html"
        email_confirmation = Mock()
        email_confirmation.key = "code123"
        email_confirmation.email_address.email = "test@example.com"
        email_confirmation.email_address.user = Mock()
        result = self.adapter.send_confirmation_mail(Mock(), email_confirmation, signup=False)
        assert result == "code123"
        assert mock_send_mail.called

    @patch.object(JWTAllAuthAdapter, "format_email_subject", side_effect=lambda s: "Formatted: " + s)
    @patch.object(JWTAllAuthAdapter, "get_from_email", return_value="from@example.com")
    @patch("oxutils.auth.adapter.render_to_string")
    @patch("oxutils.auth.adapter.get_current_site")
    def test_render_mail_html_only(
        self, mock_get_current_site, mock_render_to_string, mock_from_email, mock_fmt_subject,
        mock_allauth_context, mock_allauth_app_settings
    ):
        mock_allauth_app_settings.TEMPLATE_EXTENSION = "html"
        mock_allauth_context.request = Mock()
        mock_get_current_site.return_value = Mock(domain="example.com", name="Example")
        mock_render_to_string.return_value = "Rendered content"
        msg = self.adapter.render_mail(
            "account/email/test", "test@example.com", {"user": Mock()},
            template_path="custom/template.html",
        )
        assert msg.subject is not None
        assert msg.to == ["test@example.com"]

    @patch.object(JWTAllAuthAdapter, "format_email_subject", side_effect=lambda s: "Formatted: " + s)
    @patch.object(JWTAllAuthAdapter, "get_from_email", return_value="from@example.com")
    @patch("oxutils.auth.adapter.render_to_string")
    @patch("oxutils.auth.adapter.get_current_site")
    def test_render_mail_multipart(
        self, mock_get_current_site, mock_render_to_string, mock_from_email, mock_fmt_subject,
        mock_allauth_context, mock_allauth_app_settings
    ):
        mock_allauth_app_settings.TEMPLATE_EXTENSION = "html"
        mock_allauth_context.request = Mock()
        mock_get_current_site.return_value = Mock(domain="example.com", name="Example")
        mock_render_to_string.return_value = "Rendered content"
        msg = self.adapter.render_mail(
            "account/email/test", "test@example.com", {"user": Mock()},
        )
        assert msg.subject is not None

    @patch.object(JWTAllAuthAdapter, "format_email_subject", side_effect=lambda s: "Formatted: " + s)
    @patch.object(JWTAllAuthAdapter, "get_from_email", return_value="from@example.com")
    @patch("oxutils.auth.adapter.render_to_string")
    @patch("oxutils.auth.adapter.get_current_site")
    def test_render_mail_with_headers(
        self, mock_get_current_site, mock_render_to_string, mock_from_email, mock_fmt_subject,
        mock_allauth_context, mock_allauth_app_settings
    ):
        mock_allauth_app_settings.TEMPLATE_EXTENSION = "html"
        mock_allauth_context.request = Mock()
        mock_get_current_site.return_value = Mock(domain="example.com", name="Example")
        mock_render_to_string.return_value = "Rendered content"
        msg = self.adapter.render_mail(
            "account/email/test", "test@example.com", {"user": Mock()},
            headers={"X-Custom": "value"},
        )
        assert msg.subject is not None

    @patch.object(JWTAllAuthAdapter, "format_email_subject", side_effect=lambda s: "Formatted: " + s)
    @patch.object(JWTAllAuthAdapter, "get_from_email", return_value="from@example.com")
    @patch("oxutils.auth.adapter.render_to_string")
    @patch("oxutils.auth.adapter.get_current_site")
    def test_render_mail_with_multiple_recipients(
        self, mock_get_current_site, mock_render_to_string, mock_from_email, mock_fmt_subject,
        mock_allauth_context, mock_allauth_app_settings
    ):
        mock_allauth_app_settings.TEMPLATE_EXTENSION = "html"
        mock_allauth_context.request = Mock()
        mock_get_current_site.return_value = Mock(domain="example.com", name="Example")
        mock_render_to_string.return_value = "Rendered content"
        msg = self.adapter.render_mail(
            "account/email/test", ["user1@example.com", "user2@example.com"], {"user": Mock()},
        )
        assert msg.to == ["user1@example.com", "user2@example.com"]

    @patch.object(JWTAllAuthAdapter, "format_email_subject", side_effect=lambda s: "Formatted: " + s)
    @patch.object(JWTAllAuthAdapter, "get_from_email", return_value="from@example.com")
    @patch("oxutils.auth.adapter.render_to_string", return_value="Rendered")
    @patch("oxutils.auth.adapter.get_current_site")
    def test_render_mail_falls_back_to_txt(
        self, mock_get_current_site, mock_render_to_string, mock_from_email, mock_fmt_subject,
        mock_allauth_context, mock_allauth_app_settings
    ):
        mock_allauth_app_settings.TEMPLATE_EXTENSION = "html"
        mock_allauth_context.request = Mock()
        mock_get_current_site.return_value = Mock(domain="example.com", name="Example")
        msg = self.adapter.render_mail(
            "account/email/test", "test@example.com", {"user": Mock()},
        )
        assert msg.subject is not None

    @patch.object(JWTAllAuthAdapter, "format_email_subject", side_effect=lambda s: "Formatted: " + s)
    @patch.object(JWTAllAuthAdapter, "get_from_email", return_value="from@example.com")
    @patch("oxutils.auth.adapter.render_to_string", return_value="Rendered")
    @patch("oxutils.auth.adapter.get_current_site")
    def test_render_mail_subject_formatting(
        self, mock_get_current_site, mock_render_to_string, mock_from_email, mock_fmt_subject,
        mock_allauth_context, mock_allauth_app_settings
    ):
        mock_allauth_app_settings.TEMPLATE_EXTENSION = "html"
        mock_allauth_context.request = Mock()
        mock_get_current_site.return_value = Mock(domain="example.com", name="Example")
        msg = self.adapter.render_mail(
            "account/email/test", "test@example.com", {"user": Mock()},
            subject_path="custom/subject.txt",
        )
        assert msg.subject is not None
