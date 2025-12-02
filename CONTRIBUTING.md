# Contributing to OxUtils

Thank you for your interest in contributing to OxUtils! 🎉

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/oxiliere/oxutils.git
cd oxutils

# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check src/
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

- Write clean, documented code
- Follow existing code style
- Add type hints
- Write docstrings for public functions

### 3. Write Tests

```bash
# Add tests in tests/
# Run tests
uv run pytest

# Check coverage
uv run pytest --cov=oxutils --cov-report=term-missing
```

### 4. Update Documentation

- Update relevant `.md` files in `docs/`
- Update `CHANGELOG.md` under `[Unreleased]`
- Add docstrings to new functions/classes

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
# or
git commit -m "fix: resolve bug"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style

### Python Style

- Follow PEP 8
- Line length: 100 characters
- Use type hints
- Write docstrings (Google style)

```python
def my_function(param: str) -> dict:
    """Short description.
    
    Longer description if needed.
    
    Args:
        param: Description of param
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something is wrong
    """
    return {"result": param}
```

### Linting

```bash
# Check code
uv run ruff check src/

# Auto-fix issues
uv run ruff check --fix src/

# Format code
uv run ruff format src/
```

## Testing

### Running Tests

```bash
# All tests
uv run pytest

# Specific file
uv run pytest tests/test_jwt.py

# With coverage
uv run pytest --cov=oxutils --cov-report=html

# Verbose
uv run pytest -v
```

### Writing Tests

- Use `pytest` fixtures
- Mock external dependencies
- Test edge cases
- Keep tests isolated

```python
import pytest
from oxutils.jwt.client import verify_token

def test_verify_valid_token(valid_token):
    """Test verification of valid token."""
    payload = verify_token(valid_token)
    assert 'sub' in payload
```

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def process_data(data: dict, validate: bool = True) -> dict:
    """Process input data.
    
    Args:
        data: Input data dictionary
        validate: Whether to validate data
        
    Returns:
        Processed data dictionary
        
    Raises:
        ValidationException: If validation fails
    """
```

### Documentation Files

- Keep docs concise (50-200 lines per file)
- Include code examples
- Update when adding features

## Pull Request Guidelines

### Before Submitting

- ✅ All tests pass
- ✅ Code is linted
- ✅ Documentation is updated
- ✅ CHANGELOG.md is updated
- ✅ Type hints are added
- ✅ No merge conflicts

### PR Description

Include:
- What changed
- Why it changed
- How to test it
- Related issues (if any)

### Review Process

1. Automated tests run via GitHub Actions
2. Code review by maintainers
3. Requested changes (if any)
4. Approval and merge

## Release Process

Maintainers only:

1. Update version in `pyproject.toml` and `src/oxutils/__init__.py`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.1.0`
4. Push tag: `git push origin v0.1.0`
5. GitHub Actions publishes to PyPI

## Questions?

- Open an [issue](https://github.com/oxiliere/oxutils/issues)
- Email: eddycondor07@gmail.com

## Code of Conduct

Be respectful, inclusive, and professional.

---

Thank you for contributing! 🚀
