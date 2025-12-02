# OxUtils Tests

**126 tests - 100% passing ✅**

## Coverage

| Module | Tests |
|--------|-------|
| Enums | 8 |
| Exceptions | 32 |
| Functions | 22 |
| JWT | 17 |
| Mixins | 12 |
| S3 | 18 |
| Settings | 17 |

## Running Tests

```bash
# All tests
uv run pytest

# Specific module
uv run pytest tests/test_jwt.py

# With coverage
uv run pytest --cov=oxutils --cov-report=html

# Verbose
uv run pytest -v
```

## Fixtures (conftest.py)

- `request_factory` - Django RequestFactory
- `sample_jwt_payload` - Sample JWT payload
- `temp_jwt_key` - Temporary RSA key pair

## Writing New Tests

```python
import pytest
from unittest.mock import patch

class TestMyFeature:
    def test_basic(self):
        result = my_function()
        assert result == expected
    
    @patch('module.external')
    def test_with_mock(self, mock_ext):
        mock_ext.return_value = "mocked"
        assert my_function() == "mocked"
```

## Key Features

- ✅ **Fast** - ~2 seconds for full suite
- ✅ **Isolated** - No external dependencies
- ✅ **Mocked** - No real AWS/Auth calls
- ✅ **Type-safe** - Full type hints

---

**All tests passing ✅**
