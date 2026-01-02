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

## Environment Setup

Create a `.env` file:

```bash
# Service
OXI_SERVICE_NAME=my-service

# JWT
OXI_JWT_JWKS_URL=https://auth.example.com/.well-known/jwks.json

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
