"""
Tests for context processors
"""
import pytest
from unittest.mock import Mock, patch
from oxutils.context.site_name_processor import site_name


class TestSiteNameProcessor:
    """Tests for site_name context processor"""

    @patch('oxutils.settings.oxi_settings')
    def test_site_name_processor_returns_correct_context(self, mock_settings):
        """Test that site_name processor returns site_name and site_domain"""
        # Arrange
        mock_settings.site_name = "Test Site"
        mock_settings.site_domain = "test.example.com"
        mock_request = Mock()

        # Act
        result = site_name(mock_request)

        # Assert
        assert 'site_name' in result
        assert 'site_domain' in result
        assert result['site_name'] == "Test Site"
        assert result['site_domain'] == "test.example.com"

    @patch('oxutils.settings.oxi_settings')
    def test_site_name_processor_with_empty_values(self, mock_settings):
        """Test site_name processor with empty values"""
        # Arrange
        mock_settings.site_name = ""
        mock_settings.site_domain = ""
        mock_request = Mock()

        # Act
        result = site_name(mock_request)

        # Assert
        assert result['site_name'] == ""
        assert result['site_domain'] == ""

    @patch('oxutils.settings.oxi_settings')
    def test_site_name_processor_with_none_values(self, mock_settings):
        """Test site_name processor with None values"""
        # Arrange
        mock_settings.site_name = None
        mock_settings.site_domain = None
        mock_request = Mock()

        # Act
        result = site_name(mock_request)

        # Assert
        assert result['site_name'] is None
        assert result['site_domain'] is None

    @patch('oxutils.settings.oxi_settings')
    def test_site_name_processor_request_not_used(self, mock_settings):
        """Test that the request parameter is not used in the processor"""
        # Arrange
        mock_settings.site_name = "Site"
        mock_settings.site_domain = "domain.com"

        # Act - pass None as request since it's not used
        result = site_name(None)

        # Assert
        assert result['site_name'] == "Site"
        assert result['site_domain'] == "domain.com"
