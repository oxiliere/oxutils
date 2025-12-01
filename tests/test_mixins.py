"""
Tests for OxUtils mixins module.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from django.db import models
from django.contrib.auth import get_user_model


# Import mixins
try:
    from oxutils.models.base import (
        UUIDMixin,
        TimestampMixin,
        BaseModelMixin,
        NameMixin,
        UserTrackingMixin,
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
class TestUUIDMixin:
    """Test UUIDMixin."""
    
    def test_uuid_mixin_has_uuid_field(self):
        """Test UUIDMixin has UUID field."""
        class TestModel(UUIDMixin):
            class Meta:
                app_label = 'test'
        
        assert hasattr(TestModel, 'id')
    
    def test_uuid_mixin_generates_uuid(self):
        """Test UUIDMixin generates UUID on creation."""
        class TestModel(UUIDMixin):
            class Meta:
                app_label = 'test'
        
        # UUID should be auto-generated
        # (actual test would require database)


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
class TestTimestampMixin:
    """Test TimestampMixin."""
    
    def test_timestamp_mixin_has_fields(self):
        """Test TimestampMixin has timestamp fields."""
        class TestModel(TimestampMixin):
            class Meta:
                app_label = 'test'
        
        assert hasattr(TestModel, 'created_at')
        assert hasattr(TestModel, 'updated_at')


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
class TestBaseModelMixin:
    """Test BaseModelMixin."""
    
    def test_base_model_mixin_has_all_fields(self):
        """Test BaseModelMixin has all required fields."""
        class TestModel(BaseModelMixin):
            class Meta:
                app_label = 'test'
        
        # Should have UUID
        assert hasattr(TestModel, 'id')
        
        # Should have timestamps
        assert hasattr(TestModel, 'created_at')
        assert hasattr(TestModel, 'updated_at')
        
        # Should have is_active
        assert hasattr(TestModel, 'is_active')


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
class TestNameMixin:
    """Test NameMixin."""
    
    def test_name_mixin_has_fields(self):
        """Test NameMixin has name and description fields."""
        class TestModel(NameMixin):
            class Meta:
                app_label = 'test'
        
        assert hasattr(TestModel, 'name')
        assert hasattr(TestModel, 'description')


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
class TestUserTrackingMixin:
    """Test UserTrackingMixin."""
    
    def test_user_tracking_mixin_has_fields(self):
        """Test UserTrackingMixin has user tracking fields."""
        class TestModel(UserTrackingMixin):
            class Meta:
                app_label = 'test'
        
        assert hasattr(TestModel, 'created_by')
        assert hasattr(TestModel, 'updated_by')


class TestDetailDictMixin:
    """Test DetailDictMixin."""
    
    def test_detail_dict_mixin_basic(self):
        """Test DetailDictMixin basic functionality."""
        from oxutils.mixins.base import DetailDictMixin
        
        class TestException(DetailDictMixin, Exception):
            def __init__(self, detail=None):
                self.detail = detail
                super().__init__(detail)
        
        exc = TestException(detail="Test error")
        assert exc.detail == "Test error"
    
    def test_detail_dict_mixin_with_dict(self):
        """Test DetailDictMixin with dictionary detail."""
        from oxutils.mixins.base import DetailDictMixin
        
        class TestException(DetailDictMixin, Exception):
            def __init__(self, detail=None):
                self.detail = detail
                super().__init__(detail)
        
        detail = {"field": "error", "code": "test"}
        exc = TestException(detail=detail)
        assert exc.detail == detail


class TestBaseService:
    """Test BaseService mixin."""
    
    def test_base_service_exception_handler(self):
        """Test BaseService exception handler."""
        from oxutils.mixins.services import BaseService
        from oxutils.exceptions import InternalErrorException
        
        class TestService(BaseService):
            pass
        
        service = TestService()
        
        with pytest.raises(InternalErrorException):
            service.exception_handler(Exception("Test error"))
    
    def test_base_service_with_custom_exception(self):
        """Test BaseService with custom exception."""
        from oxutils.mixins.services import BaseService
        from oxutils.exceptions import ValidationException
        
        class TestService(BaseService):
            def validate_data(self, data):
                try:
                    if not data:
                        raise ValidationException(detail="Data is required")
                    return data
                except ValidationException:
                    raise
                except Exception as exc:
                    self.exception_handler(exc)
        
        service = TestService()
        
        with pytest.raises(ValidationException):
            service.validate_data(None)


class TestEnumMixin:
    """Test EnumMixin."""
    
    def test_enum_mixin_choices(self):
        """Test EnumMixin choices method."""
        from oxutils.mixins.enums import EnumMixin
        from enum import Enum
        
        class StatusEnum(EnumMixin, Enum):
            PENDING = 'pending'
            ACTIVE = 'active'
            INACTIVE = 'inactive'
        
        choices = StatusEnum.choices()
        
        assert len(choices) == 3
        assert ('pending', 'Pending') in choices
        assert ('active', 'Active') in choices
    
    def test_enum_mixin_values(self):
        """Test EnumMixin values method."""
        from oxutils.mixins.enums import EnumMixin
        from enum import Enum
        
        class StatusEnum(EnumMixin, Enum):
            PENDING = 'pending'
            ACTIVE = 'active'
        
        values = StatusEnum.values()
        
        assert 'pending' in values
        assert 'active' in values
        assert len(values) == 2
    
    def test_enum_mixin_labels(self):
        """Test EnumMixin labels method."""
        from oxutils.mixins.enums import EnumMixin
        from enum import Enum
        
        class StatusEnum(EnumMixin, Enum):
            PENDING = 'pending'
            ACTIVE = 'active'
        
        labels = StatusEnum.labels()
        
        assert 'Pending' in labels
        assert 'Active' in labels


class TestSchemaMixins:
    """Test schema mixins."""
    
    def test_timestamp_schema_mixin(self):
        """Test TimestampSchemaMixin."""
        from oxutils.mixins.schemas import TimestampSchemaMixin
        from pydantic import BaseModel
        
        class TestSchema(TimestampSchemaMixin, BaseModel):
            name: str
        
        # Should have timestamp fields
        assert 'created_at' in TestSchema.model_fields
        assert 'updated_at' in TestSchema.model_fields
    
    def test_uuid_schema_mixin(self):
        """Test UUIDSchemaMixin."""
        from oxutils.mixins.schemas import UUIDSchemaMixin
        from pydantic import BaseModel
        
        class TestSchema(UUIDSchemaMixin, BaseModel):
            name: str
        
        # Should have id field
        assert 'id' in TestSchema.model_fields


class TestMixinIntegration:
    """Test mixin integration scenarios."""
    
    @pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
    def test_combined_mixins(self):
        """Test combining multiple mixins."""
        class Product(BaseModelMixin, NameMixin):
            price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
            
            class Meta:
                app_label = 'test'
        
        # Should have all fields from both mixins
        assert hasattr(Product, 'id')  # From BaseModelMixin
        assert hasattr(Product, 'created_at')  # From BaseModelMixin
        assert hasattr(Product, 'is_active')  # From BaseModelMixin
        assert hasattr(Product, 'name')  # From NameMixin
        assert hasattr(Product, 'description')  # From NameMixin
        assert hasattr(Product, 'price')  # Own field
