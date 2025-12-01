"""
Tests for OxUtils utility functions.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from io import BytesIO
from ninja_extra.exceptions import ValidationError
from oxutils.functions import (
    get_absolute_url,
    request_is_bound,
    get_request_data,
    validate_image,
)


class TestGetAbsoluteUrl:
    """Test get_absolute_url function."""
    
    def test_get_absolute_url_with_request(self, request_factory):
        """Test get_absolute_url with request object."""
        request = request_factory.get('/')
        url = get_absolute_url('/media/image.jpg', request)
        
        assert url.startswith('http://')
        assert '/media/image.jpg' in url
    
    def test_get_absolute_url_without_request(self):
        """Test get_absolute_url without request object."""
        with patch('oxutils.functions.settings') as mock_settings:
            mock_settings.SITE_URL = 'http://example.com'
            url = get_absolute_url('/media/image.jpg')
            
            assert url == 'http://example.com/media/image.jpg'
    
    def test_get_absolute_url_default_fallback(self):
        """Test get_absolute_url with default fallback."""
        with patch('oxutils.functions.settings') as mock_settings:
            mock_settings.SITE_URL = None
            delattr(mock_settings, 'SITE_URL')
            
            url = get_absolute_url('/media/image.jpg')
            assert 'localhost' in url


class TestRequestIsBound:
    """Test request_is_bound function."""
    
    def test_request_is_bound_with_post_data(self, request_factory):
        """Test request_is_bound with POST data."""
        request = request_factory.post('/', {'key': 'value'})
        assert request_is_bound(request) is True
    
    def test_request_is_bound_with_post_method(self, request_factory):
        """Test request_is_bound with POST method."""
        request = request_factory.post('/')
        assert request_is_bound(request) is True
    
    def test_request_is_bound_with_get_method(self, request_factory):
        """Test request_is_bound with GET method."""
        request = request_factory.get('/')
        assert request_is_bound(request) is False
    
    def test_request_is_bound_with_drf_request(self):
        """Test request_is_bound with DRF-style request."""
        request = Mock()
        request.method = 'POST'
        request.data = {'key': 'value'}
        
        assert request_is_bound(request) is True
    
    def test_request_is_bound_with_files(self, request_factory):
        """Test request_is_bound with FILES."""
        request = request_factory.post('/')
        request.FILES = {'file': 'test'}
        
        assert request_is_bound(request) is True
    
    def test_request_is_bound_with_none(self):
        """Test request_is_bound with None."""
        assert request_is_bound(None) is False
    
    def test_request_is_bound_without_method(self):
        """Test request_is_bound without method attribute."""
        request = Mock(spec=[])
        assert request_is_bound(request) is False


class TestGetRequestData:
    """Test get_request_data function."""
    
    def test_get_request_data_with_post(self, request_factory):
        """Test get_request_data with POST data."""
        request = request_factory.post('/', {'key': 'value'})
        data = get_request_data(request)
        
        assert 'key' in data
    
    def test_get_request_data_with_drf_request(self):
        """Test get_request_data with DRF-style request."""
        request = Mock()
        request.data = {'key': 'value', 'email': 'test@example.com'}
        
        data = get_request_data(request)
        
        assert data == {'key': 'value', 'email': 'test@example.com'}
    
    def test_get_request_data_with_none(self):
        """Test get_request_data with None."""
        data = get_request_data(None)
        assert data == {}
    
    def test_get_request_data_empty_post(self, request_factory):
        """Test get_request_data with empty POST."""
        request = request_factory.post('/')
        data = get_request_data(request)
        
        assert data == {}
    
    def test_get_request_data_get_request(self, request_factory):
        """Test get_request_data with GET request."""
        request = request_factory.get('/')
        data = get_request_data(request)
        
        assert data == {}


class TestValidateImage:
    """Test validate_image function."""
    
    def create_mock_image(self, size_mb=1, content_type='image/jpeg', filename='test.jpg'):
        """Helper to create mock uploaded image."""
        mock_file = Mock()
        mock_file.size = size_mb * 1024 * 1024
        mock_file.content_type = content_type
        mock_file.name = filename
        mock_file.seek = Mock()
        mock_file.read = Mock(return_value=b'fake image data')
        return mock_file
    
    def test_validate_image_success(self):
        """Test validate_image with valid image."""
        mock_file = self.create_mock_image(size_mb=1)
        
        with patch('oxutils.functions.Image') as mock_image:
            mock_image.open.return_value.verify.return_value = None
            
            # Should not raise
            validate_image(mock_file, size=2)
    
    def test_validate_image_file_too_large(self):
        """Test validate_image with file too large."""
        mock_file = self.create_mock_image(size_mb=3)
        
        with pytest.raises(ValidationError, match="taille du fichier"):
            validate_image(mock_file, size=2)
    
    def test_validate_image_invalid_content_type(self):
        """Test validate_image with invalid content type."""
        mock_file = self.create_mock_image(
            size_mb=1,
            content_type='application/pdf'
        )
        
        with pytest.raises(ValidationError, match="Type de fichier non supporté"):
            validate_image(mock_file, size=2)
    
    def test_validate_image_invalid_extension(self):
        """Test validate_image with invalid extension."""
        mock_file = self.create_mock_image(
            size_mb=1,
            filename='test.pdf'
        )
        
        with pytest.raises(ValidationError, match="Extension de fichier non supportée"):
            validate_image(mock_file, size=2)
    
    def test_validate_image_allowed_types(self):
        """Test validate_image with all allowed types."""
        allowed_types = [
            ('image/jpeg', 'test.jpg'),
            ('image/jpg', 'test.jpg'),
            ('image/png', 'test.png'),
            ('image/gif', 'test.gif'),
            ('image/webp', 'test.webp'),
        ]
        
        with patch('oxutils.functions.Image') as mock_image:
            mock_image.open.return_value.verify.return_value = None
            
            for content_type, filename in allowed_types:
                mock_file = self.create_mock_image(
                    size_mb=1,
                    content_type=content_type,
                    filename=filename
                )
                # Should not raise
                validate_image(mock_file, size=2)
    
    def test_validate_image_corrupted_file(self):
        """Test validate_image with corrupted image file."""
        mock_file = self.create_mock_image(size_mb=1)
        
        with patch('oxutils.functions.Image') as mock_image:
            mock_image.open.side_effect = Exception("Corrupted image")
            
            with pytest.raises(ValidationError, match="pas une image valide"):
                validate_image(mock_file, size=2)
    
    def test_validate_image_custom_size_limit(self):
        """Test validate_image with custom size limit."""
        mock_file = self.create_mock_image(size_mb=4)
        
        # Should fail with 2MB limit
        with pytest.raises(ValidationError):
            validate_image(mock_file, size=2)
        
        # Should succeed with 5MB limit
        with patch('oxutils.functions.Image') as mock_image:
            mock_image.open.return_value.verify.return_value = None
            validate_image(mock_file, size=5)
