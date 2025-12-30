# OxUtils Tests

Structure organisée par module avec settings isolés.

## Structure

```
tests/
├── oxiliere/
│   ├── settings.py          # Settings avec tenant models
│   ├── test_oxiliere.py
│   └── test_permissions.py
├── permissions/
│   ├── settings.py          # Settings pour permissions
│   └── test_permissions.py
├── common/
│   ├── settings.py          # Settings communs
│   └── test_*.py            # Tous les autres tests
└── conftest.py              # Configuration pytest principale
```

## Exécution des tests

Pour exécuter les tests d'un module spécifique, utiliser l'option `--ds` :

```bash
# Tests permissions
pytest tests/permissions/ --ds=tests.permissions.settings

# Tests oxiliere
pytest tests/oxiliere/ --ds=tests.oxiliere.settings

# Tests common
pytest tests/common/ --ds=tests.common.settings
```

Ou définir la variable d'environnement :

```bash
# Tests permissions
DJANGO_SETTINGS_MODULE=tests.permissions.settings pytest tests/permissions/

# Tests oxiliere
DJANGO_SETTINGS_MODULE=tests.oxiliere.settings pytest tests/oxiliere/

# Tests common
DJANGO_SETTINGS_MODULE=tests.common.settings pytest tests/common/
```

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
