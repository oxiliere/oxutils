# Migrations Management Guide

This document explains how to create and manage migrations for the **oxutils** reusable Django application.

## Creating Migrations

### Method 1: Using the Provided Script (Recommended)

A `make_migrations.py` script is provided at the project root to facilitate migration creation:

```bash
uv run python make_migrations.py
```

This script:
- Automatically configures the minimal Django environment
- Sets the required environment variables for S3
- Generates migrations for the `oxutils.audit` module

### Method 2: From an Existing Django Project

If you are integrating oxutils into an existing Django project:

1. Add oxutils apps to `INSTALLED_APPS` (the audit module is included in `UTILS_APPS`):

```python
# settings.py
from oxutils.conf import UTILS_APPS

INSTALLED_APPS = [
    *UTILS_APPS,  # Includes 'oxutils.audit' and other dependencies
    # ... other apps
]
```

Alternatively, you can add it manually:

```python
INSTALLED_APPS = [
    # ... other apps
    'oxutils.audit',
]
```

2. Configure the required environment variables:

```bash
export OXI_SERVICE_NAME=your-service
export OXI_USE_LOG_S3=True
export OXI_USE_PRIVATE_S3=True
export OXI_USE_PRIVATE_S3_AS_LOG=True
export OXI_PRIVATE_S3_STORAGE_BUCKET_NAME=your-bucket
export OXI_PRIVATE_S3_ACCESS_KEY_ID=your-key
export OXI_PRIVATE_S3_SECRET_ACCESS_KEY=your-secret
export OXI_PRIVATE_S3_S3_CUSTOM_DOMAIN=your-domain.com
```

3. Create the migrations:

```bash
python manage.py makemigrations audit
```

## Migration Structure

Migrations are stored in:
```
src/oxutils/audit/migrations/
├── __init__.py
└── 0001_initial.py
```

## Included Models

The migrations create the following tables:

### LogExportState
- `id`: Primary key
- `created_at`: Creation date
- `updated_at`: Last modification date
- `last_export_date`: Last export date
- `status`: Export status (PENDING, SUCCESS, FAILED)
- `data`: File stored on S3
- `size`: File size in bytes

### LogExportHistory
- `id`: Primary key
- `state`: Reference to LogExportState
- `status`: History status
- `created_at`: Creation date

## Applying Migrations

In your Django project:

```bash
python manage.py migrate audit
```

## Important Notes

1. **Reusable Application**: oxutils is designed as a reusable Django application. Migrations are included in the package.

2. **S3 Configuration**: The models use S3 storage for files. Make sure your S3 configuration is correct before applying migrations.

3. **Dependencies**: The migrations have no external dependencies (no `dependencies` in the initial migration).

4. **Tests**: Migrations are automatically applied when running tests via pytest-django.

## Troubleshooting

### Error: "Missing required log S3 configuration"

Make sure all S3 environment variables are defined:
- `OXI_USE_LOG_S3=True`
- `OXI_USE_PRIVATE_S3=True`
- `OXI_USE_PRIVATE_S3_AS_LOG=True`
- `OXI_PRIVATE_S3_STORAGE_BUCKET_NAME`
- `OXI_PRIVATE_S3_ACCESS_KEY_ID`
- `OXI_PRIVATE_S3_SECRET_ACCESS_KEY`
- `OXI_PRIVATE_S3_S3_CUSTOM_DOMAIN`

### Error: "No module named 'oxutils'"

Verify that the `src/` path is in your PYTHONPATH or use the provided script.

## Resources

- [Django documentation on migrations](https://docs.djangoproject.com/en/stable/topics/migrations/)
- [Django reusable applications](https://docs.djangoproject.com/en/stable/intro/reusable-apps/)
