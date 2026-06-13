"""
Tests for oxutils.auth.templatetags module.
"""
import pytest
from unittest.mock import Mock, patch


class TestSpaUrlTag:
    """Tests for spa_url template tag."""

    @patch("oxutils.auth.templatetags.spa_urls.format_confirm_email_url")
    def test_confirm_email_url_type(self, mock_format):
        from oxutils.auth.templatetags.spa_urls import spa_url

        mock_format.return_value = "https://app.example.com/confirm/abc"
        result = spa_url("confirm_email", key="abc")
        assert result == "https://app.example.com/confirm/abc"
        mock_format.assert_called_once_with("abc")

    @patch("oxutils.auth.templatetags.spa_urls.format_reset_password_url")
    def test_reset_password_url_type(self, mock_format):
        from oxutils.auth.templatetags.spa_urls import spa_url

        mock_format.return_value = "https://app.example.com/reset/uid/token"
        result = spa_url("reset_password", uidb64="uid123", key="token456")
        assert result == "https://app.example.com/reset/uid/token"
        mock_format.assert_called_once_with("uid123", "token456")

    def test_invalid_url_type_raises(self):
        from oxutils.auth.templatetags.spa_urls import spa_url

        with pytest.raises(ValueError, match="Invalid URL Type"):
            spa_url("unknown_type")

    def test_register_is_template_library(self):
        from oxutils.auth.templatetags.spa_urls import register
        from django.template import Library

        assert isinstance(register, Library)

    @patch("oxutils.auth.templatetags.spa_urls.format_confirm_email_url")
    def test_confirm_email_without_key(self, mock_format):
        from oxutils.auth.templatetags.spa_urls import spa_url

        mock_format.return_value = ""
        result = spa_url("confirm_email")
        assert result == ""

    @patch("oxutils.auth.templatetags.spa_urls.format_reset_password_url")
    def test_reset_password_without_params(self, mock_format):
        from oxutils.auth.templatetags.spa_urls import spa_url

        mock_format.return_value = ""
        result = spa_url("reset_password")
        assert result == ""
