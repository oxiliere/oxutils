"""
Tests for OxUtils enums module.
"""
import pytest
from oxutils.enums import ExportStatus


class TestExportStatus:
    """Test ExportStatus enum."""
    
    def test_export_status_values(self):
        """Test ExportStatus has all required values."""
        assert ExportStatus.PENDING.value == 'pending'
        assert ExportStatus.PROCESSING.value == 'processing'
        assert ExportStatus.COMPLETED.value == 'completed'
        assert ExportStatus.FAILED.value == 'failed'
    
    def test_export_status_choices(self):
        """Test ExportStatus choices method."""
        choices = ExportStatus.choices()
        
        assert len(choices) == 4
        assert ('pending', 'Pending') in choices
        assert ('processing', 'Processing') in choices
        assert ('completed', 'Completed') in choices
        assert ('failed', 'Failed') in choices
    
    def test_export_status_values_method(self):
        """Test ExportStatus values method."""
        values = ExportStatus.values()
        
        assert 'pending' in values
        assert 'processing' in values
        assert 'completed' in values
        assert 'failed' in values
        assert len(values) == 4
    
    def test_export_status_labels(self):
        """Test ExportStatus labels method."""
        labels = ExportStatus.labels()
        
        assert 'Pending' in labels
        assert 'Processing' in labels
        assert 'Completed' in labels
        assert 'Failed' in labels
    
    def test_export_status_comparison(self):
        """Test ExportStatus enum comparison."""
        assert ExportStatus.PENDING == ExportStatus.PENDING
        assert ExportStatus.PENDING != ExportStatus.COMPLETED
    
    def test_export_status_in_list(self):
        """Test ExportStatus in list."""
        valid_statuses = [
            ExportStatus.PENDING,
            ExportStatus.PROCESSING,
        ]
        
        assert ExportStatus.PENDING in valid_statuses
        assert ExportStatus.COMPLETED not in valid_statuses
    
    def test_export_status_string_representation(self):
        """Test ExportStatus string representation."""
        assert str(ExportStatus.PENDING.value) == 'pending'
        assert str(ExportStatus.COMPLETED.value) == 'completed'


class TestEnumMixin:
    """Test EnumMixin functionality."""
    
    def test_enum_mixin_inheritance(self):
        """Test that ExportStatus inherits from EnumMixin."""
        from oxutils.mixins.enums import EnumMixin
        
        # ExportStatus should have EnumMixin methods
        assert hasattr(ExportStatus, 'choices')
        assert hasattr(ExportStatus, 'values')
        assert hasattr(ExportStatus, 'labels')
    
    def test_enum_choices_format(self):
        """Test that choices are in correct format for Django."""
        choices = ExportStatus.choices()
        
        # Each choice should be a tuple of (value, label)
        for choice in choices:
            assert isinstance(choice, tuple)
            assert len(choice) == 2
            assert isinstance(choice[0], str)  # value
            assert isinstance(choice[1], str)  # label
    
    def test_enum_values_are_strings(self):
        """Test that all enum values are strings."""
        values = ExportStatus.values()
        
        for value in values:
            assert isinstance(value, str)
    
    def test_enum_labels_are_capitalized(self):
        """Test that labels are properly capitalized."""
        labels = ExportStatus.labels()
        
        for label in labels:
            assert label[0].isupper()  # First letter should be uppercase


class TestEnumUsage:
    """Test enum usage in different contexts."""
    
    def test_enum_in_django_model_field(self):
        """Test using enum in Django model field."""
        from django.db import models
        
        class TestModel(models.Model):
            status = models.CharField(
                max_length=20,
                choices=ExportStatus.choices(),
                default=ExportStatus.PENDING.value
            )
            
            class Meta:
                app_label = 'test'
        
        # Should not raise any errors
        assert TestModel._meta.get_field('status').choices == ExportStatus.choices()
    
    def test_enum_validation(self):
        """Test enum value validation."""
        valid_values = ExportStatus.values()
        
        # Valid values
        assert 'pending' in valid_values
        assert 'completed' in valid_values
        
        # Invalid values
        assert 'invalid' not in valid_values
        assert 'unknown' not in valid_values
    
    def test_enum_iteration(self):
        """Test iterating over enum."""
        statuses = list(ExportStatus)
        
        assert len(statuses) == 4
        assert ExportStatus.PENDING in statuses
        assert ExportStatus.PROCESSING in statuses
        assert ExportStatus.COMPLETED in statuses
        assert ExportStatus.FAILED in statuses
    
    def test_enum_access_by_name(self):
        """Test accessing enum by name."""
        status = ExportStatus['PENDING']
        assert status == ExportStatus.PENDING
        assert status.value == 'pending'
    
    def test_enum_access_by_value(self):
        """Test accessing enum by value."""
        status = ExportStatus('pending')
        assert status == ExportStatus.PENDING


class TestCustomEnumCreation:
    """Test creating custom enums with EnumMixin."""
    
    def test_create_custom_enum(self):
        """Test creating a custom enum with EnumMixin."""
        from oxutils.mixins.enums import EnumMixin
        from enum import Enum
        
        class PriorityEnum(EnumMixin, Enum):
            LOW = 'low'
            MEDIUM = 'medium'
            HIGH = 'high'
            URGENT = 'urgent'
        
        # Test choices
        choices = PriorityEnum.choices()
        assert len(choices) == 4
        assert ('low', 'Low') in choices
        
        # Test values
        values = PriorityEnum.values()
        assert 'low' in values
        assert 'urgent' in values
        
        # Test labels
        labels = PriorityEnum.labels()
        assert 'Low' in labels
        assert 'Urgent' in labels
