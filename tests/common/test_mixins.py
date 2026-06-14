"""
Tests for OxUtils mixins module — behavior only, not field existence.
"""
import pytest


class TestDetailDictMixin:
    """Test DetailDictMixin — exception formatting behavior."""

    def test_custom_detail_overrides_default(self):
        from oxutils.mixins.base import DetailDictMixin

        class TestException(DetailDictMixin, Exception):
            default_detail = "Default error"
            default_code = "default_error"

            def __init__(self, detail=None, code=None):
                super().__init__(detail=detail, code=code)

        exc = TestException(detail="Custom message")
        assert exc.args[0]["detail"] == "Custom message"
        assert exc.args[0]["code"] == "default_error"

    def test_dict_detail_merges_with_defaults(self):
        from oxutils.mixins.base import DetailDictMixin

        class TestException(DetailDictMixin, Exception):
            default_detail = "Default error"
            default_code = "default_error"

            def __init__(self, detail=None, code=None):
                super().__init__(detail=detail, code=code)

        exc = TestException(detail={"field": "invalid", "extra": "info"})
        assert exc.args[0]["field"] == "invalid"
        assert exc.args[0]["extra"] == "info"
        assert exc.args[0]["code"] == "default_error"

    def test_custom_code(self):
        from oxutils.mixins.base import DetailDictMixin

        class TestException(DetailDictMixin, Exception):
            default_detail = "Default"
            default_code = "default_error"

            def __init__(self, detail=None, code=None):
                super().__init__(detail=detail, code=code)

        exc = TestException(code="custom_error")
        assert exc.args[0]["code"] == "custom_error"


class TestBaseService:
    """Test BaseService — exception handling."""

    def test_exception_handler_wraps_unknown_errors(self):
        from oxutils.mixins.services import BaseService
        from oxutils.exceptions import InternalErrorException

        class TestService(BaseService):
            pass

        with pytest.raises(InternalErrorException):
            TestService().exception_handler(Exception("Test error"))

    def test_custom_exceptions_pass_through(self):
        from oxutils.mixins.services import BaseService
        from oxutils.exceptions import ValidationException

        class TestService(BaseService):
            def validate(self, data):
                try:
                    if not data:
                        raise ValidationException(detail="Data is required")
                    return data
                except ValidationException:
                    raise
                except Exception as exc:
                    self.exception_handler(exc)

        with pytest.raises(ValidationException):
            TestService().validate(None)
