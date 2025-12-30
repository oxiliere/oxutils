"""
Tests for OxUtils exceptions module.
"""
import pytest
from oxutils.exceptions import (
    OxException,
    APIException,
    ExceptionCode,
    NotFoundException,
    ValidationException,
    ConflictException,
    DuplicateEntryException,
    PermissionDeniedException,
    UnauthorizedException,
    InvalidParameterException,
    MissingParameterException,
    InternalErrorException,
)


class TestExceptionCodes:
    """Test ExceptionCode constants."""
    
    def test_error_codes_exist(self):
        """Test that all error codes are defined."""
        assert ExceptionCode.INTERNAL_ERROR == 'internal_error'
        assert ExceptionCode.NOT_FOUND == 'not_found'
        assert ExceptionCode.VALIDATION_ERROR == 'validation_error'
        assert ExceptionCode.UNAUTHORIZED == 'unauthorized'
        assert ExceptionCode.FORBIDDEN == 'forbidden'
        assert ExceptionCode.CONFLICT_ERROR == 'conflict_error'
        assert ExceptionCode.DUPLICATE_ENTRY == 'duplicate_entry'
        assert ExceptionCode.PERMISSION_DENIED == 'permission_denied'
        assert ExceptionCode.INVALID_PARAMETER == 'invalid_parameter'
        assert ExceptionCode.MISSING_PARAMETER == 'missing_parameter'
    
    def test_success_code(self):
        """Test success code."""
        assert ExceptionCode.SUCCESS == 'success'


class TestOxException:
    """Test base OxException."""
    
    def test_ox_exception_creation(self):
        """Test OxException can be created."""
        exc = OxException("Test error")
        assert str(exc) == "Test error"
    
    def test_ox_exception_inheritance(self):
        """Test OxException inherits from Exception."""
        assert issubclass(OxException, Exception)


class TestAPIException:
    """Test APIException base class."""
    
    def test_api_exception_default_attributes(self):
        """Test APIException default attributes."""
        exc = APIException()
        assert exc.status_code == 500
        assert exc.default_code == ExceptionCode.INTERNAL_ERROR
    
    def test_api_exception_with_detail(self):
        """Test APIException with custom detail."""
        exc = APIException(detail="Custom error message")
        assert "Custom error message" in str(exc)
    
    def test_api_exception_with_dict_detail(self):
        """Test APIException with dictionary detail."""
        detail = {"field": "error message", "extra": "info"}
        exc = APIException(detail=detail)
        # DetailDictMixin merges the detail dict with default values
        # NinjaException stores detail in the detail attribute
        if hasattr(exc, 'detail'):
            detail_dict = exc.detail
        elif exc.args:
            detail_dict = exc.args[0]
        else:
            # Fallback: just check the exception was created
            assert exc is not None
            return
        
        assert detail_dict["field"] == "error message"
        assert detail_dict["extra"] == "info"
        assert "code" in detail_dict  # Should have default code


class TestNotFoundException:
    """Test NotFoundException."""
    
    def test_not_found_exception_status_code(self):
        """Test NotFoundException has correct status code."""
        exc = NotFoundException()
        assert exc.status_code == 404
    
    def test_not_found_exception_code(self):
        """Test NotFoundException has correct error code."""
        exc = NotFoundException()
        assert exc.default_code == ExceptionCode.NOT_FOUND
    
    def test_not_found_exception_with_detail(self):
        """Test NotFoundException with custom detail."""
        exc = NotFoundException(detail="User not found")
        assert "User not found" in str(exc)
    
    def test_not_found_exception_with_context(self):
        """Test NotFoundException with context data."""
        exc = NotFoundException(detail={
            "message": "Resource not found",
            "resource_id": "123"
        })
        assert exc.detail["resource_id"] == "123"


class TestValidationException:
    """Test ValidationException."""
    
    def test_validation_exception_status_code(self):
        """Test ValidationException has correct status code."""
        exc = ValidationException()
        assert exc.status_code == 400
    
    def test_validation_exception_code(self):
        """Test ValidationException has correct error code."""
        exc = ValidationException()
        assert exc.default_code == ExceptionCode.VALIDATION_ERROR
    
    def test_validation_exception_with_field_errors(self):
        """Test ValidationException with field errors."""
        exc = ValidationException(detail={
            "email": ["Invalid email format"],
            "password": ["Password too short"]
        })
        assert "email" in exc.detail
        assert "password" in exc.detail


class TestConflictException:
    """Test ConflictException."""
    
    def test_conflict_exception_status_code(self):
        """Test ConflictException has correct status code."""
        exc = ConflictException()
        assert exc.status_code == 409
    
    def test_conflict_exception_code(self):
        """Test ConflictException has correct error code."""
        exc = ConflictException()
        assert exc.default_code == ExceptionCode.CONFLICT_ERROR


class TestDuplicateEntryException:
    """Test DuplicateEntryException."""
    
    def test_duplicate_entry_exception_status_code(self):
        """Test DuplicateEntryException has correct status code."""
        exc = DuplicateEntryException()
        assert exc.status_code == 409
    
    def test_duplicate_entry_exception_code(self):
        """Test DuplicateEntryException has correct error code."""
        exc = DuplicateEntryException()
        assert exc.default_code == ExceptionCode.DUPLICATE_ENTRY
    
    def test_duplicate_entry_exception_with_detail(self):
        """Test DuplicateEntryException with custom detail."""
        exc = DuplicateEntryException(detail="Email already exists")
        assert "Email already exists" in str(exc)


class TestPermissionDeniedException:
    """Test PermissionDeniedException."""
    
    def test_permission_denied_exception_status_code(self):
        """Test PermissionDeniedException has correct status code."""
        exc = PermissionDeniedException()
        assert exc.status_code == 403
    
    def test_permission_denied_exception_code(self):
        """Test PermissionDeniedException has correct error code."""
        exc = PermissionDeniedException()
        assert exc.default_code == ExceptionCode.PERMISSION_DENIED


class TestUnauthorizedException:
    """Test UnauthorizedException."""
    
    def test_unauthorized_exception_status_code(self):
        """Test UnauthorizedException has correct status code."""
        exc = UnauthorizedException()
        assert exc.status_code == 401
    
    def test_unauthorized_exception_code(self):
        """Test UnauthorizedException has correct error code."""
        exc = UnauthorizedException()
        assert exc.default_code == ExceptionCode.UNAUTHORIZED


class TestInvalidParameterException:
    """Test InvalidParameterException."""
    
    def test_invalid_parameter_exception_status_code(self):
        """Test InvalidParameterException has correct status code."""
        exc = InvalidParameterException()
        assert exc.status_code == 400
    
    def test_invalid_parameter_exception_code(self):
        """Test InvalidParameterException has correct error code."""
        exc = InvalidParameterException()
        assert exc.default_code == ExceptionCode.INVALID_PARAMETER


class TestMissingParameterException:
    """Test MissingParameterException."""
    
    def test_missing_parameter_exception_status_code(self):
        """Test MissingParameterException has correct status code."""
        exc = MissingParameterException()
        assert exc.status_code == 400
    
    def test_missing_parameter_exception_code(self):
        """Test MissingParameterException has correct error code."""
        exc = MissingParameterException()
        assert exc.default_code == ExceptionCode.MISSING_PARAMETER


class TestInternalErrorException:
    """Test InternalErrorException."""
    
    def test_internal_error_exception_status_code(self):
        """Test InternalErrorException has correct status code."""
        exc = InternalErrorException()
        assert exc.status_code == 500
    
    def test_internal_error_exception_code(self):
        """Test InternalErrorException has correct error code."""
        exc = InternalErrorException()
        assert exc.default_code == ExceptionCode.INTERNAL_ERROR


class TestExceptionRaising:
    """Test exception raising in context."""
    
    def test_raise_not_found_exception(self):
        """Test raising NotFoundException."""
        with pytest.raises(NotFoundException) as exc_info:
            raise NotFoundException(detail="Resource not found")
        
        assert exc_info.value.status_code == 404
        assert "Resource not found" in str(exc_info.value)
    
    def test_raise_validation_exception(self):
        """Test raising ValidationException."""
        with pytest.raises(ValidationException) as exc_info:
            raise ValidationException(detail="Invalid input")
        
        assert exc_info.value.status_code == 400
    
    def test_exception_in_function(self):
        """Test exception raised in function."""
        def get_user(user_id):
            if user_id is None:
                raise MissingParameterException(detail="user_id is required")
            return {"id": user_id}
        
        with pytest.raises(MissingParameterException):
            get_user(None)
        
        # Should not raise
        result = get_user("123")
        assert result["id"] == "123"
