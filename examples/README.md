# OxUtils Examples

This directory contains practical examples of using OxUtils in Django projects.

## Examples

### 1. [basic_setup.py](basic_setup.py)
Complete Django settings configuration with OxUtils.

**Covers:**
- Installing apps and middleware
- S3 configuration
- Celery setup
- Logging configuration

### 2. [jwt_auth.py](jwt_auth.py)
JWT authentication with Django Ninja.

**Covers:**
- Creating JWT authentication class
- Protected endpoints
- Public endpoints
- Accessing user data from token

### 3. [s3_storage.py](s3_storage.py)
Using S3 storage backends.

**Covers:**
- Public media storage
- Private media storage with presigned URLs
- Access control
- Direct storage operations

## Environment Setup

Create a `.env` file:

```bash
# Service
OXI_SERVICE_NAME=my-service

# JWT
OXI_JWT_JWKS_URL=https://auth.example.com/.well-known/jwks.json

# S3
OXI_USE_STATIC_S3=True
OXI_STATIC_STORAGE_BUCKET_NAME=my-bucket
OXI_STATIC_S3_CUSTOM_DOMAIN=cdn.example.com

OXI_USE_DEFAULT_S3=True
OXI_USE_STATIC_S3_AS_DEFAULT=True

OXI_USE_PRIVATE_S3=True
OXI_PRIVATE_S3_STORAGE_BUCKET_NAME=private-bucket

# Audit
OXI_LOG_ACCESS=True
OXI_RETENTION_DELAY=30
```

## Running Examples

These are code snippets for reference. To use them:

1. Copy the relevant code to your Django project
2. Configure environment variables
3. Run migrations: `python manage.py migrate`
4. Start server: `python manage.py runserver`

## More Information

See the [main documentation](../docs/) for detailed guides on each module.
