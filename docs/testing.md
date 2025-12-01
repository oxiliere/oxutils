# Testing Documentation

Comprehensive testing guide for OxUtils.

## Overview

OxUtils uses **pytest** as the testing framework with comprehensive test coverage across all modules. Tests are organized by module and include unit tests, integration tests, and fixtures for common scenarios.

### Test Coverage

- ✅ **Settings Module** - Configuration and validation
- ✅ **Exceptions Module** - Custom exceptions and error codes
- ✅ **Functions Module** - Utility functions
- ✅ **JWT Module** - Token verification and authentication
- ✅ **Mixins Module** - Model, service, and schema mixins
- ✅ **Enums Module** - Standardized enumerations

---

## Table of Contents

- [Installation](#installation)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Writing Tests](#writing-tests)
- [Fixtures](#fixtures)
- [Coverage Reports](#coverage-reports)
- [Continuous Integration](#continuous-integration)
- [Best Practices](#best-practices)

---

## Installation

### Install Test Dependencies

```bash
# Using uv
uv sync --dev

# Or using pip
pip install -e ".[dev]"
```

### Test Dependencies

- `pytest>=8.0.0` - Testing framework
- `pytest-django>=4.8.0` - Django integration
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-mock>=3.12.0` - Mocking utilities
- `coverage>=7.4.0` - Coverage measurement

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_settings.py

# Run specific test class
pytest tests/test_settings.py::TestOxUtilsSettings

# Run specific test
pytest tests/test_settings.py::TestOxUtilsSettings::test_settings_initialization
```

### Using Makefile

```bash
# Run all tests
make test

# Run with verbose output
make test-verbose

# Run with coverage
make test-coverage

# Run fast (no coverage)
make test-fast

# Run specific module tests
make test-settings
make test-jwt
make test-exceptions
```

### Test Markers

```bash
# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration

# Exclude slow tests
pytest -m "not slow"

# Run tests requiring database
pytest -m django_db
```

### Pattern Matching

```bash
# Run tests matching pattern
pytest -k "jwt"
pytest -k "validation"
pytest -k "test_settings or test_jwt"
```

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── pytest.ini               # Pytest settings
├── settings.py              # Django settings for tests
├── README.md                # Test documentation
├── test_settings.py         # Settings module tests (18 tests)
├── test_exceptions.py       # Exceptions module tests (25 tests)
├── test_functions.py        # Functions module tests (15 tests)
├── test_jwt.py              # JWT module tests (12 tests)
├── test_mixins.py           # Mixins module tests (10 tests)
└── test_enums.py            # Enums module tests (8 tests)
```

### Test Count by Module

| Module | Tests | Coverage |
|--------|-------|----------|
| Settings | 18 | Configuration, validation, Django integration |
| Exceptions | 25 | All exception types, error codes |
| Functions | 15 | URL building, request handling, validation |
| JWT | 12 | Token verification, JWKS, local keys |
| Mixins | 10 | Model mixins, service mixins, schemas |
| Enums | 8 | ExportStatus, EnumMixin functionality |
| **Total** | **88+** | **Comprehensive coverage** |

---

## Test Structure

### Settings Tests (`test_settings.py`)

```python
class TestOxUtilsSettings:
    """Test OxUtilsSettings configuration."""
    
    def test_settings_initialization(self):
        """Test basic settings initialization."""
        settings = OxUtilsSettings(service_name='test-service')
        assert settings.service_name == 'test-service'
    
    def test_s3_validation_missing_credentials(self):
        """Test S3 validation fails with missing credentials."""
        with pytest.raises(ValueError):
            OxUtilsSettings(service_name='test', use_static_s3=True)
```

**Coverage:**
- ✅ Basic initialization
- ✅ Default values (JWT, Audit, S3)
- ✅ S3 validation (success and failure)
- ✅ JWT key validation
- ✅ Dependency validation
- ✅ URL generation methods
- ✅ Environment variable loading
- ✅ Django settings integration

### Exceptions Tests (`test_exceptions.py`)

```python
class TestNotFoundException:
    """Test NotFoundException."""
    
    def test_not_found_exception_status_code(self):
        """Test NotFoundException has correct status code."""
        exc = NotFoundException()
        assert exc.status_code == 404
```

**Coverage:**
- ✅ All exception types (9 exceptions)
- ✅ Error codes (30+ codes)
- ✅ Exception attributes
- ✅ Custom details
- ✅ Dictionary details
- ✅ Exception raising
- ✅ Context data

### Functions Tests (`test_functions.py`)

```python
class TestValidateImage:
    """Test validate_image function."""
    
    def test_validate_image_file_too_large(self):
        """Test validate_image with file too large."""
        mock_file = self.create_mock_image(size_mb=3)
        
        with pytest.raises(ValidationError):
            validate_image(mock_file, size=2)
```

**Coverage:**
- ✅ URL generation (with/without request)
- ✅ Request binding detection
- ✅ Request data extraction
- ✅ Image validation (size, type, extension)
- ✅ Corrupted file handling
- ✅ Custom size limits

### JWT Tests (`test_jwt.py`)

```python
class TestTokenVerification:
    """Test JWT token verification."""
    
    def test_verify_token_success(self, temp_jwt_key):
        """Test successful token verification."""
        token = jwt.encode(payload, private_key, algorithm='RS256')
        verified = verify_token(token)
        assert verified['sub'] == 'user-123'
```

**Coverage:**
- ✅ JWKS fetching and caching
- ✅ Public key retrieval
- ✅ Token verification (success/failure)
- ✅ Expired tokens
- ✅ Invalid signatures
- ✅ Missing kid
- ✅ Local key authentication

### Mixins Tests (`test_mixins.py`)

```python
class TestBaseModelMixin:
    """Test BaseModelMixin."""
    
    def test_base_model_mixin_has_all_fields(self):
        """Test BaseModelMixin has all required fields."""
        assert hasattr(TestModel, 'id')
        assert hasattr(TestModel, 'created_at')
        assert hasattr(TestModel, 'is_active')
```

**Coverage:**
- ✅ UUIDMixin
- ✅ TimestampMixin
- ✅ BaseModelMixin
- ✅ NameMixin
- ✅ UserTrackingMixin
- ✅ DetailDictMixin
- ✅ BaseService
- ✅ EnumMixin
- ✅ Schema mixins

### Enums Tests (`test_enums.py`)

```python
class TestExportStatus:
    """Test ExportStatus enum."""
    
    def test_export_status_choices(self):
        """Test ExportStatus choices method."""
        choices = ExportStatus.choices()
        assert ('pending', 'Pending') in choices
```

**Coverage:**
- ✅ Enum values
- ✅ Choices method
- ✅ Values method
- ✅ Labels method
- ✅ Enum comparison
- ✅ Django integration
- ✅ Custom enum creation

---

## Writing Tests

### Basic Test Structure

```python
import pytest
from oxutils.module import function_to_test


class TestFeature:
    """Test feature description."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        input_data = "test"
        
        # Act
        result = function_to_test(input_data)
        
        # Assert
        assert result == expected_value
```

### Testing Exceptions

```python
import pytest
from oxutils.exceptions import NotFoundException


def test_exception_raised():
    """Test that exception is raised."""
    with pytest.raises(NotFoundException) as exc_info:
        raise NotFoundException(detail="Not found")
    
    assert exc_info.value.status_code == 404
    assert "Not found" in str(exc_info.value)
```

### Using Fixtures

```python
def test_with_fixture(mock_request):
    """Test using fixture."""
    result = process_request(mock_request)
    assert result is not None
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
    ("test3", "result3"),
])
def test_multiple_inputs(input, expected):
    """Test with multiple inputs."""
    result = function_to_test(input)
    assert result == expected
```

### Using Mocks

```python
from unittest.mock import Mock, patch


def test_with_mock():
    """Test with mock."""
    with patch('oxutils.module.external_function') as mock_func:
        mock_func.return_value = "mocked"
        
        result = function_to_test()
        
        assert result == "mocked"
        mock_func.assert_called_once()
```

---

## Fixtures

Common fixtures are defined in `conftest.py`:

### Request Fixtures

```python
@pytest.fixture
def request_factory():
    """Provide Django RequestFactory."""
    return RequestFactory()

@pytest.fixture
def mock_request(request_factory):
    """Provide a mock HTTP request."""
    request = request_factory.get('/')
    request.user = Mock()
    request.user.id = 'test-user-id'
    return request
```

### JWT Fixtures

```python
@pytest.fixture
def sample_jwt_payload():
    """Provide a sample JWT payload."""
    return {
        'sub': 'user-123',
        'email': 'test@example.com',
        'exp': 9999999999,
    }

@pytest.fixture
def temp_jwt_key(tmp_path):
    """Create temporary JWT key files for testing."""
    # Creates RSA key pair and returns paths
```

### S3 Fixtures

```python
@pytest.fixture
def mock_s3_client():
    """Provide a mock boto3 S3 client."""
    client = MagicMock()
    client.put_object.return_value = {'ETag': '"test-etag"'}
    return client
```

### Logger Fixtures

```python
@pytest.fixture
def mock_structlog_logger():
    """Provide a mock structlog logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    return logger
```

---

## Coverage Reports

### Generate Coverage Report

```bash
# Terminal report
pytest --cov=oxutils --cov-report=term-missing

# HTML report
pytest --cov=oxutils --cov-report=html

# XML report (for CI)
pytest --cov=oxutils --cov-report=xml
```

### View HTML Report

```bash
# Generate report
make test-coverage

# Open in browser
open htmlcov/index.html
```

### Coverage Goals

- **Overall Coverage**: > 80%
- **Critical Modules**: > 90%
  - Settings
  - JWT
  - Exceptions
- **Utility Modules**: > 75%
  - Functions
  - Mixins

---

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Pull requests
- Pushes to `main` and `develop` branches
- Release tags

### CI Configuration

```yaml
# .github/workflows/tests.yml
- name: Run tests with coverage
  run: |
    uv run pytest --cov=oxutils --cov-report=xml
```

### Coverage Upload

Coverage reports are uploaded to Codecov for tracking over time.

---

## Best Practices

### 1. Test Naming

```python
# ✅ Good - Descriptive name
def test_validate_image_file_too_large():
    """Test validate_image with file too large."""

# ❌ Bad - Vague name
def test_validation():
    """Test validation."""
```

### 2. One Assertion Per Test

```python
# ✅ Good - Single assertion
def test_status_code():
    """Test exception status code."""
    exc = NotFoundException()
    assert exc.status_code == 404

def test_error_code():
    """Test exception error code."""
    exc = NotFoundException()
    assert exc.default_code == ExceptionCode.NOT_FOUND

# ❌ Bad - Multiple unrelated assertions
def test_exception():
    exc = NotFoundException()
    assert exc.status_code == 404
    assert exc.default_code == ExceptionCode.NOT_FOUND
    assert "not found" in str(exc)
```

### 3. Arrange-Act-Assert

```python
def test_get_absolute_url():
    """Test absolute URL generation."""
    # Arrange
    request = request_factory.get('/')
    url_path = '/media/image.jpg'
    
    # Act
    result = get_absolute_url(url_path, request)
    
    # Assert
    assert result.startswith('http://')
    assert url_path in result
```

### 4. Use Fixtures

```python
# ✅ Good - Use fixture
def test_with_fixture(mock_request):
    result = process_request(mock_request)
    assert result is not None

# ❌ Bad - Recreate setup
def test_without_fixture():
    request = Mock()
    request.user = Mock()
    request.user.id = 'test-user-id'
    result = process_request(request)
    assert result is not None
```

### 5. Mock External Dependencies

```python
# ✅ Good - Mock external calls
@patch('oxutils.jwt.client.requests.get')
def test_fetch_jwks(mock_get):
    mock_get.return_value.json.return_value = {'keys': []}
    jwks = fetch_jwks('https://example.com/jwks')
    assert 'keys' in jwks

# ❌ Bad - Real external calls
def test_fetch_jwks():
    jwks = fetch_jwks('https://example.com/jwks')  # Real HTTP call
    assert 'keys' in jwks
```

### 6. Test Edge Cases

```python
def test_validate_image_edge_cases():
    """Test image validation edge cases."""
    # Empty file
    # Maximum size
    # Minimum size
    # Invalid extension
    # Corrupted file
```

### 7. Keep Tests Fast

```python
# ✅ Good - Fast unit test
def test_exception_code():
    exc = NotFoundException()
    assert exc.default_code == ExceptionCode.NOT_FOUND

# ❌ Bad - Slow integration test without marker
def test_database_query():
    # Database operations without @pytest.mark.slow
```

---

## Troubleshooting

### Django Not Configured

```bash
export DJANGO_SETTINGS_MODULE=tests.settings
pytest
```

### Import Errors

```bash
# Install in development mode
pip install -e .
```

### Database Errors

```python
@pytest.mark.django_db
def test_with_database():
    """Test requiring database."""
    pass
```

### Coverage Not Working

```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Run with coverage
pytest --cov=oxutils
```

---

## Related Documentation

- [Settings Documentation](./settings.md) - Configuration testing
- [JWT Documentation](./jwt.md) - Authentication testing
- [Exceptions Documentation](./misc.md) - Exception testing

---

## Support

For questions or issues regarding testing, please contact the Oxiliere development team or open an issue in the repository.
