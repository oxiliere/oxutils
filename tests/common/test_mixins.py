"""
Tests for OxUtils mixins module.
"""
import pytest
from django.db import models


# Import mixins
try:
    from oxutils.models.base import (
        UUIDPrimaryKeyMixin,
        TimestampMixin,
        BaseModelMixin,
        NameMixin,
        UserTrackingMixin,
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
class TestUUIDPrimaryKeyMixin:
    """Test UUIDPrimaryKeyMixin."""
    
    def test_uuid_mixin_has_uuid_field(self):
        """Test UUIDPrimaryKeyMixin has UUID field."""
        class UUIDTestModel(UUIDPrimaryKeyMixin):
            class Meta:
                app_label = 'test'
        
        assert hasattr(UUIDTestModel, 'id')
    
    def test_uuid_mixin_generates_uuid(self):
        """Test UUIDPrimaryKeyMixin generates UUID on creation."""
        class UUIDGenerateTestModel(UUIDPrimaryKeyMixin):
            class Meta:
                app_label = 'test'
        
        # UUID should be auto-generated
        # (actual test would require database)


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
class TestTimestampMixin:
    """Test TimestampMixin."""
    
    def test_timestamp_mixin_has_fields(self):
        """Test TimestampMixin has timestamp fields."""
        class TimestampTestModel(TimestampMixin):
            class Meta:
                app_label = 'test'
        
        assert hasattr(TimestampTestModel, 'created_at')
        assert hasattr(TimestampTestModel, 'updated_at')


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
class TestBaseModelMixin:
    """Test BaseModelMixin."""
    
    def test_base_model_mixin_has_all_fields(self):
        """Test BaseModelMixin has all required fields."""
        class BaseModelTestModel(BaseModelMixin):
            class Meta:
                app_label = 'test'
        
        # Should have UUID
        assert hasattr(BaseModelTestModel, 'id')
        
        # Should have timestamps
        assert hasattr(BaseModelTestModel, 'created_at')
        assert hasattr(BaseModelTestModel, 'updated_at')
        
        # Should have is_active
        assert hasattr(BaseModelTestModel, 'is_active')


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
class TestNameMixin:
    """Test NameMixin."""
    
    def test_name_mixin_has_fields(self):
        """Test NameMixin has name and description fields."""
        class NameMixinTestModel(NameMixin):
            class Meta:
                app_label = 'test'
        
        assert hasattr(NameMixinTestModel, 'name')
        assert hasattr(NameMixinTestModel, 'description')


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
class TestUserTrackingMixin:
    """Test UserTrackingMixin."""
    
    def test_user_tracking_mixin_has_fields(self):
        """Test UserTrackingMixin has user tracking fields."""
        class UserTrackingTestModel(UserTrackingMixin):
            class Meta:
                app_label = 'test'
        
        assert hasattr(UserTrackingTestModel, 'created_by')
        assert hasattr(UserTrackingTestModel, 'updated_by')


class TestDetailDictMixin:
    """Test DetailDictMixin."""
    
    def test_detail_dict_mixin_basic(self):
        """Test DetailDictMixin basic functionality."""
        from oxutils.mixins.base import DetailDictMixin
        
        class TestException(DetailDictMixin, Exception):
            default_detail = "Default error"
            default_code = "default_error"
            
            def __init__(self, detail=None, code=None):
                super().__init__(detail=detail, code=code)
        
        exc = TestException(detail="Test error")
        detail_dict = exc.args[0]
        assert detail_dict["detail"] == "Test error"
        assert detail_dict["code"] == "default_error"
    
    def test_detail_dict_mixin_with_dict(self):
        """Test DetailDictMixin with dictionary detail."""
        from oxutils.mixins.base import DetailDictMixin
        
        class TestException(DetailDictMixin, Exception):
            default_detail = "Default error"
            default_code = "default_error"
            
            def __init__(self, detail=None, code=None):
                super().__init__(detail=detail, code=code)
        
        detail = {"field": "error", "extra": "info"}
        exc = TestException(detail=detail)
        detail_dict = exc.args[0]
        assert detail_dict["field"] == "error"
        assert detail_dict["extra"] == "info"


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




class TestSchemaMixins:
    """Test schema mixins."""
    
    def test_response_schema(self):
        """Test ResponseSchema."""
        from oxutils.mixins.schemas import ResponseSchema
        
        # Should have required fields
        assert 'detail' in ResponseSchema.model_fields
        assert 'code' in ResponseSchema.model_fields
        assert 'errors' in ResponseSchema.model_fields


class TestMixinIntegration:
    """Test mixin integration scenarios."""
    
    @pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
    def test_combined_mixins(self):
        """Test combining multiple mixins."""
        class ProductTestModel(BaseModelMixin, NameMixin):
            price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
            
            class Meta:
                app_label = 'test'
        
        # Should have all fields from both mixins
        assert hasattr(ProductTestModel, 'id')  # From BaseModelMixin
        assert hasattr(ProductTestModel, 'created_at')  # From BaseModelMixin
        assert hasattr(ProductTestModel, 'is_active')  # From BaseModelMixin
        assert hasattr(ProductTestModel, 'name')  # From NameMixin
        assert hasattr(ProductTestModel, 'description')  # From NameMixin
        assert hasattr(ProductTestModel, 'price')  # Own field
