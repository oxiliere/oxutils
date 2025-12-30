"""
Tests for SafeDeleteModelMixin and MaskedBackupField.
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from django.db import models
from django.test import TestCase, override_settings
from django.conf import settings


try:
    from oxutils.models.base import SafeDeleteModelMixin
    from oxutils.models.fields import MaskedBackupField, get_field_masking_fernet
    from safedelete.models import SafeDeleteModel
    SAFEDELETE_AVAILABLE = True
except ImportError:
    SAFEDELETE_AVAILABLE = False


@pytest.mark.skipif(not SAFEDELETE_AVAILABLE, reason="django-safedelete not available")
class TestMaskedBackupField:
    """Test MaskedBackupField functionality."""
    
    def test_field_initialization(self):
        """Test MaskedBackupField can be initialized."""
        field = MaskedBackupField()
        assert isinstance(field, models.TextField)
    
    @override_settings(FIELD_MASKING_CRYPTO_ENABLED=False)
    def test_field_without_encryption(self):
        """Test MaskedBackupField without encryption."""
        field = MaskedBackupField()
        
        # Test data
        test_data = {"email": "test@example.com", "name": "John Doe"}
        
        # Prepare value for database
        prepared = field.get_prep_value(test_data)
        assert prepared is not None
        assert isinstance(prepared, str)
        
        # Convert back from database
        result = field.to_python(prepared)
        assert result == test_data
    
    @override_settings(FIELD_MASKING_CRYPTO_ENABLED=False)
    def test_field_with_none_value(self):
        """Test MaskedBackupField with None value."""
        field = MaskedBackupField()
        
        prepared = field.get_prep_value(None)
        assert prepared is None
        
        result = field.to_python(None)
        assert result == {}
    
    @override_settings(FIELD_MASKING_CRYPTO_ENABLED=False)
    def test_field_with_empty_string(self):
        """Test MaskedBackupField with empty string."""
        field = MaskedBackupField()
        
        prepared = field.get_prep_value("")
        assert prepared is None
        
        result = field.to_python("")
        assert result == {}
    
    @override_settings(FIELD_MASKING_CRYPTO_ENABLED=False)
    def test_field_with_dict_input(self):
        """Test MaskedBackupField to_python with dict input."""
        field = MaskedBackupField()
        
        test_data = {"key": "value"}
        result = field.to_python(test_data)
        assert result == test_data
    
    @override_settings(FIELD_MASKING_CRYPTO_ENABLED=False)
    def test_field_with_invalid_json(self):
        """Test MaskedBackupField handles invalid JSON gracefully."""
        field = MaskedBackupField()
        
        # Invalid JSON should return empty dict
        result = field.to_python("invalid json {")
        assert result == {}
    
    @override_settings(FIELD_MASKING_CRYPTO_ENABLED=True, SECRET_KEY="test-secret-key")
    def test_field_with_encryption_fallback(self):
        """Test MaskedBackupField with encryption using SECRET_KEY fallback."""
        field = MaskedBackupField()
        
        test_data = {"sensitive": "data"}
        
        # Prepare value (should be encrypted)
        prepared = field.get_prep_value(test_data)
        assert prepared is not None
        assert isinstance(prepared, str)
        # Encrypted data should be different from plain JSON
        import json
        assert prepared != json.dumps(test_data)
        
        # Convert back (should decrypt)
        result = field.to_python(prepared)
        assert result == test_data


@pytest.mark.skipif(not SAFEDELETE_AVAILABLE, reason="django-safedelete not available")
class TestGetFieldMaskingFernet:
    """Test get_field_masking_fernet function."""
    
    @override_settings(FIELD_MASKING_CRYPTO_ENABLED=False)
    def test_disabled_encryption(self):
        """Test when encryption is disabled."""
        fernet = get_field_masking_fernet()
        assert fernet is None
    
    @override_settings(FIELD_MASKING_CRYPTO_ENABLED=True, FIELD_MASKING_KEY="LCPN2bFN2NHA6XCZscpv8JctYJQ2FTfuVKIunFUchnE=")
    def test_with_custom_key(self):
        """Test with custom FIELD_MASKING_KEY."""
        from cryptography.fernet import Fernet
        
        fernet = get_field_masking_fernet()
        assert fernet is not None
        assert isinstance(fernet, Fernet)
    
    def test_with_secret_key_fallback(self):
        """Test fallback to SECRET_KEY."""
        # Skip if FIELD_MASKING_KEY is already defined in settings
        if hasattr(settings, 'FIELD_MASKING_KEY'):
            pytest.skip("FIELD_MASKING_KEY is defined in settings, cannot test fallback")


@pytest.mark.skipif(not SAFEDELETE_AVAILABLE, reason="django-safedelete not available")
class TestSafeDeleteModelMixin(TestCase):
    """Test SafeDeleteModelMixin functionality."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create a test model
        class TestModel(SafeDeleteModelMixin):
            email = models.EmailField(unique=True)
            username = models.CharField(max_length=100, unique=True)
            slug = models.SlugField(unique=True)
            url = models.URLField()
            bio = models.CharField(max_length=255)
            age = models.IntegerField(null=True)
            
            mask_fields = ['email', 'username', 'slug', 'url', 'bio', 'age']
            
            class Meta:
                app_label = 'test'
        
        cls.TestModel = TestModel
    
    def test_mixin_has_masked_backup_field(self):
        """Test SafeDeleteModelMixin has _masked_backup field."""
        assert hasattr(self.TestModel, '_masked_backup')
    
    def test_mixin_has_mask_fields_attribute(self):
        """Test SafeDeleteModelMixin has mask_fields attribute."""
        assert hasattr(self.TestModel, 'mask_fields')
        assert isinstance(self.TestModel.mask_fields, list)
    
    def test_mask_value_email_field(self):
        """Test _mask_value for EmailField."""
        instance = self.TestModel()
        field = self.TestModel._meta.get_field('email')
        
        masked = instance._mask_value(field, "test@example.com")
        
        assert masked.endswith(".deleted@invalid.local")
        assert "@" in masked
    
    def test_mask_value_url_field(self):
        """Test _mask_value for URLField."""
        instance = self.TestModel()
        field = self.TestModel._meta.get_field('url')
        
        masked = instance._mask_value(field, "https://example.com")
        
        assert masked.startswith("https://deleted.invalid/")
    
    def test_mask_value_slug_field(self):
        """Test _mask_value for SlugField."""
        instance = self.TestModel()
        field = self.TestModel._meta.get_field('slug')
        
        masked = instance._mask_value(field, "my-slug")
        
        assert masked.startswith("deleted-")
        assert len(masked) > len("deleted-")
    
    def test_mask_value_char_field(self):
        """Test _mask_value for CharField."""
        instance = self.TestModel()
        field = self.TestModel._meta.get_field('bio')
        
        masked = instance._mask_value(field, "My bio")
        
        assert masked.startswith("__deleted__")
    
    def test_mask_value_integer_field(self):
        """Test _mask_value for IntegerField."""
        instance = self.TestModel()
        field = self.TestModel._meta.get_field('age')
        
        masked = instance._mask_value(field, 25)
        
        assert masked is None
    
    def test_mask_value_generates_unique_values(self):
        """Test _mask_value generates unique values each time."""
        instance = self.TestModel()
        field = self.TestModel._meta.get_field('email')
        
        masked1 = instance._mask_value(field, "test@example.com")
        time.sleep(0.01)  # Small delay to ensure different timestamp
        masked2 = instance._mask_value(field, "test@example.com")
        
        # Should be different due to UUID
        assert masked1 != masked2
    
    @patch.object(SafeDeleteModelMixin, 'save')
    @patch.object(SafeDeleteModel, 'delete')
    def test_delete_masks_fields(self, mock_super_delete, mock_save):
        """Test delete method masks specified fields."""
        instance = self.TestModel(
            email="test@example.com",
            username="testuser",
            slug="test-slug",
            url="https://example.com",
            bio="Test bio",
            age=25
        )
        instance.pk = 1
        
        # Mock the _meta.get_field to return actual fields
        original_email = instance.email
        
        instance.delete()
        
        # Check that fields were masked
        assert instance.email != original_email
        assert instance.email.endswith(".deleted@invalid.local")
        
        # Check that backup was created
        assert instance._masked_backup != {}
        assert 'email' in instance._masked_backup
        assert instance._masked_backup['email'] == original_email
        
        # Check that save was called
        mock_save.assert_called_once()
        
        # Check that super().delete() was called
        mock_super_delete.assert_called_once()
    
    @patch.object(SafeDeleteModelMixin, 'save')
    def test_restore_masked_fields(self, mock_save):
        """Test restore_masked_fields method."""
        instance = self.TestModel(
            email="masked@invalid.local",
            username="masked-user"
        )
        instance.pk = 1
        instance._masked_backup = {
            'email': 'original@example.com',
            'username': 'originaluser'
        }
        
        # Mock the queryset to return no conflicts
        with patch.object(self.TestModel._default_manager, 'filter') as mock_filter:
            mock_qs = MagicMock()
            mock_qs.exclude.return_value.exists.return_value = False
            mock_filter.return_value = mock_qs
            
            instance.restore_masked_fields()
        
        # Check that fields were restored
        assert instance.email == 'original@example.com'
        assert instance.username == 'originaluser'
        
        # Check that backup was cleared
        assert instance._masked_backup == {}
        
        # Check that save was called
        mock_save.assert_called_once()
    
    def test_restore_masked_fields_with_collision(self):
        """Test restore_masked_fields raises error on collision."""
        instance = self.TestModel(
            email="masked@invalid.local"
        )
        instance.pk = 1
        instance._masked_backup = {
            'email': 'original@example.com'
        }
        
        # Mock the queryset to return a conflict
        with patch.object(self.TestModel._default_manager, 'filter') as mock_filter:
            mock_qs = MagicMock()
            mock_qs.exclude.return_value.exists.return_value = True
            mock_filter.return_value = mock_qs
            
            with pytest.raises(ValueError) as exc_info:
                instance.restore_masked_fields()
            
            assert "Collision détectée" in str(exc_info.value)
    
    def test_restore_masked_fields_with_empty_backup(self):
        """Test restore_masked_fields does nothing with empty backup."""
        instance = self.TestModel(email="test@example.com")
        instance._masked_backup = {}
        
        # Should not raise any error
        instance.restore_masked_fields()
        
        # Email should remain unchanged
        assert instance.email == "test@example.com"
    
    @patch.object(SafeDeleteModelMixin, 'save')
    @patch.object(SafeDeleteModel, 'delete')
    def test_delete_skips_none_values(self, mock_super_delete, mock_save):
        """Test delete method skips None values."""
        instance = self.TestModel(
            email="test@example.com",
            username="testuser",
            slug="test-slug",
            url="https://example.com",
            bio="Test bio",
            age=None  # None value
        )
        instance.pk = 1
        
        instance.delete()
        
        # age should not be in backup since it was None
        assert 'age' not in instance._masked_backup
        
        # Other fields should be in backup
        assert 'email' in instance._masked_backup


@pytest.mark.skipif(not SAFEDELETE_AVAILABLE, reason="django-safedelete not available")
class TestSafeDeleteSignalIntegration:
    """Test signal integration for SafeDeleteModelMixin."""
    
    def test_post_undelete_signal_connected(self):
        """Test that post_undelete signal is connected."""
        from oxutils.models.base import _restore_masked_fields, post_undelete
        
        # Check that the signal handler is connected
        receivers = post_undelete.receivers
        assert len(receivers) > 0
    
    @patch.object(SafeDeleteModelMixin, 'restore_masked_fields')
    def test_signal_calls_restore_on_undelete(self, mock_restore):
        """Test that undelete signal calls restore_masked_fields."""
        from oxutils.models.base import _restore_masked_fields
        
        # Create a mock instance
        class TestModel(SafeDeleteModelMixin):
            class Meta:
                app_label = 'test'
        
        instance = TestModel()
        
        # Call the signal handler directly
        _restore_masked_fields(sender=TestModel, instance=instance)
        
        # Check that restore_masked_fields was called
        mock_restore.assert_called_once()


@pytest.mark.skipif(not SAFEDELETE_AVAILABLE, reason="django-safedelete not available")
class TestSafeDeleteModelMixinEdgeCases:
    """Test edge cases for SafeDeleteModelMixin."""
    
    @pytest.mark.django_db
    def test_empty_mask_fields(self):
        """Test SafeDeleteModelMixin with empty mask_fields."""
        class TestModel(SafeDeleteModelMixin):
            email = models.EmailField()
            mask_fields = []  # Empty list
            
            class Meta:
                app_label = 'test'
        
        instance = TestModel(email="test@example.com")
        instance.pk = 1
        
        with patch.object(SafeDeleteModel, 'delete'):
            with patch.object(SafeDeleteModelMixin, 'save'):
                instance.delete()
        
        # No fields should be masked
        assert instance._masked_backup == {}
    
    def test_nonexistent_field_in_mask_fields(self):
        """Test SafeDeleteModelMixin with nonexistent field in mask_fields."""
        class TestModel(SafeDeleteModelMixin):
            email = models.EmailField()
            mask_fields = ['nonexistent_field']
            
            class Meta:
                app_label = 'test'
        
        instance = TestModel(email="test@example.com")
        instance.pk = 1
        
        # Should raise an error when trying to get nonexistent field
        with pytest.raises(Exception):
            with patch.object(SafeDeleteModel, 'delete'):
                with patch.object(SafeDeleteModelMixin, 'save'):
                    instance.delete()
