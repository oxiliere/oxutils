"""
Tests for OxUtils enums module.
"""
from oxutils.enums.audit import ExportStatus



class TestExportStatus:
    """Test ExportStatus enum."""
    
    def test_export_status_values(self):
        """Test ExportStatus has all required values."""
        assert ExportStatus.PENDING.value == 'pending'
        assert ExportStatus.SUCCESS.value == 'success'
        assert ExportStatus.FAILED.value == 'failed'
    
    def test_export_status_comparison(self):
        """Test ExportStatus enum comparison."""
        assert ExportStatus.PENDING == ExportStatus.PENDING
        assert ExportStatus.PENDING != ExportStatus.SUCCESS
    
    def test_export_status_in_list(self):
        """Test ExportStatus in list."""
        valid_statuses = [
            ExportStatus.PENDING,
            ExportStatus.SUCCESS,
        ]
        
        assert ExportStatus.PENDING in valid_statuses
        assert ExportStatus.FAILED not in valid_statuses
    
    def test_export_status_string_representation(self):
        """Test ExportStatus string representation."""
        assert str(ExportStatus.PENDING.value) == 'pending'
        assert str(ExportStatus.SUCCESS.value) == 'success'


class TestEnumBasics:
    """Test basic enum functionality."""
    
    def test_enum_is_string(self):
        """Test that ExportStatus values are strings."""
        assert isinstance(ExportStatus.PENDING.value, str)
        assert isinstance(ExportStatus.SUCCESS.value, str)
        assert isinstance(ExportStatus.FAILED.value, str)


class TestEnumUsage:
    """Test enum usage in different contexts."""
    
    def test_enum_iteration(self):
        """Test iterating over enum."""
        statuses = list(ExportStatus)
        
        assert len(statuses) == 3
        assert ExportStatus.PENDING in statuses
        assert ExportStatus.SUCCESS in statuses
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


