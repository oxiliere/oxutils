# OxUtils Tests

Comprehensive test suite for OxUtils using pytest.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── pytest.ini               # Pytest settings
├── test_settings.py         # Settings module tests
├── test_exceptions.py       # Exceptions module tests
├── test_functions.py        # Utility functions tests
├── test_jwt.py              # JWT authentication tests
├── test_mixins.py           # Mixins tests
└── test_enums.py            # Enums tests
```

## Running Tests

### Run all tests

```bash
pytest
```

### Run specific test file

```bash
pytest tests/test_settings.py
pytest tests/test_jwt.py
```

### Run specific test class

```bash
pytest tests/test_settings.py::TestOxUtilsSettings
```

### Run specific test

```bash
pytest tests/test_settings.py::TestOxUtilsSettings::test_settings_initialization
```

### Run with coverage

```bash
pytest --cov=oxutils --cov-report=html
```

### Run with verbose output

```bash
pytest -v
```

### Run tests matching pattern

```bash
pytest -k "jwt"
pytest -k "validation"
```

## Test Markers

Tests are organized with markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.django_db` - Tests requiring database

### Run tests by marker

```bash
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

## Fixtures

Common fixtures are defined in `conftest.py`:

- `request_factory` - Django RequestFactory
- `mock_request` - Mock HTTP request
- `sample_jwt_payload` - Sample JWT payload
- `mock_s3_client` - Mock boto3 S3 client
- `temp_jwt_key` - Temporary JWT key files
- `mock_celery_app` - Mock Celery app
- `mock_structlog_logger` - Mock structlog logger

## Test Coverage

Generate coverage report:

```bash
pytest --cov=oxutils --cov-report=html
```

View coverage report:

```bash
open htmlcov/index.html
```

## Writing Tests

### Basic Test Structure

```python
import pytest
from oxutils.module import function_to_test


class TestFeature:
    """Test feature description."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = function_to_test()
        assert result == expected_value
    
    def test_with_fixture(self, mock_request):
        """Test using fixture."""
        result = function_to_test(mock_request)
        assert result is not None
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
```

### Using Mocks

```python
from unittest.mock import Mock, patch


def test_with_mock():
    """Test with mock."""
    with patch('oxutils.module.function') as mock_func:
        mock_func.return_value = "mocked"
        result = function_to_test()
        assert result == "mocked"
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

## Continuous Integration

Tests are run automatically on:

- Pull requests
- Commits to main branch
- Release tags

## Troubleshooting

### Django not configured

If you see "Django not configured" errors:

```bash
export DJANGO_SETTINGS_MODULE=tests.settings
pytest
```

### Import errors

Ensure oxutils is installed in development mode:

```bash
pip install -e .
```

### Database errors

For tests requiring database:

```python
@pytest.mark.django_db
def test_with_database():
    """Test requiring database."""
    pass
```

## Best Practices

1. **One assertion per test** - Keep tests focused
2. **Use descriptive names** - Test names should describe what they test
3. **Arrange-Act-Assert** - Structure tests clearly
4. **Use fixtures** - Reuse common setup code
5. **Mock external dependencies** - Don't call real APIs or databases
6. **Test edge cases** - Test boundary conditions and error cases
7. **Keep tests fast** - Unit tests should run in milliseconds

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
