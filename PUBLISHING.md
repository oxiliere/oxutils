# Publishing Guide

## Prerequisites

- PyPI account: https://pypi.org/account/register/
- PyPI token configured
- All tests passing: `uv run pytest`

## Pre-publication Checklist

- [ ] All tests pass (126/126)
- [ ] Version updated in `pyproject.toml` and `src/oxutils/__init__.py`
- [ ] `CHANGELOG.md` updated
- [ ] Documentation up to date
- [ ] No secrets in code
- [ ] LICENSE present

## Publishing Steps

### 1. Verify Version

```bash
# Check version consistency
grep version pyproject.toml
grep __version__ src/oxutils/__init__.py
```

### 2. Update CHANGELOG.md

```markdown
## [0.1.0] - 2024-12-02

### Added
- List of new features
```

### 3. Test Build

```bash
# Build the package
uv build

# Check contents
tar -tzf dist/oxutils-0.1.0.tar.gz | head -20
```

### 4. Test Local Installation

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate

# Install from wheel
pip install dist/oxutils-0.1.0-py3-none-any.whl

# Test import
python -c "import oxutils; print(oxutils.__version__)"

# Cleanup
deactivate
rm -rf test_env
```

### 5. Publish to Test PyPI (Optional)

```bash
# Configure Test PyPI
export UV_PUBLISH_URL=https://test.pypi.org/legacy/
export UV_PUBLISH_TOKEN=your-test-pypi-token

# Publish
uv publish

# Test installation
pip install --index-url https://test.pypi.org/simple/ oxutils
```

### 6. Publish to PyPI

```bash
# Configure PyPI
export UV_PUBLISH_TOKEN=your-pypi-token

# Publish
uv publish

# Or with twine
uv run twine upload dist/*
```

### 7. Create Git Tag

```bash
# Create tag
git tag -a v0.1.0 -m "Release version 0.1.0"

# Push tag
git push origin v0.1.0
```

### 8. Create GitHub Release

1. Go to https://github.com/oxiliere/oxutils/releases/new
2. Select tag `v0.1.0`
3. Title: `v0.1.0`
4. Description: Copy from CHANGELOG.md
5. Publish

## Automatic Publishing via GitHub Actions

The `.github/workflows/publish.yml` workflow automatically publishes to PyPI when a GitHub release is created.

### Configuration

1. Create PyPI token: https://pypi.org/manage/account/token/
2. Add token to GitHub Secrets:
   - Name: `PYPI_API_TOKEN`
   - Value: `pypi-...`

### Usage

```bash
# Create and push tag
git tag v0.1.0
git push origin v0.1.0

# Create GitHub release
# Workflow will automatically publish to PyPI
```

## Post-publication Verification

```bash
# Check on PyPI
open https://pypi.org/project/oxutils/

# Install from PyPI
pip install oxutils

# Test
python -c "import oxutils; print(oxutils.__version__)"
```

## Rollback in Case of Issues

PyPI does not allow deleting versions. If there's a problem:

1. Publish a new patch version (e.g., 0.1.1)
2. Mark the problematic version as "yanked" on PyPI

## Version Strategy

### Patch (0.1.1)
- Bug fixes only
- No breaking changes

### Minor (0.2.0)
- New features
- Backward compatible

### Major (1.0.0)
- Breaking changes
- API changes

## Support

For issues: eddycondor07@gmail.com
