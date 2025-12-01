"""
Pytest configuration and fixtures for OxUtils tests.
"""
import os
import pytest
from django.conf import settings
from django.test import RequestFactory
from unittest.mock import Mock, MagicMock


# Configure Django settings for tests
def pytest_configure():
    """Configure Django settings for pytest."""
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
                'django_structlog',
                'auditlog',
                'cid.apps.CidAppConfig',
                'django_celery_results',
            ],
            MIDDLEWARE=[
                'cid.middleware.CidMiddleware',
                'auditlog.middleware.AuditlogMiddleware',
                'django_structlog.middlewares.RequestMiddleware',
            ],
            SECRET_KEY='test-secret-key',
            USE_TZ=True,
            ROOT_URLCONF='',
        )
        
        import django
        django.setup()


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
    request.user.is_authenticated = True
    return request


@pytest.fixture
def sample_jwt_payload():
    """Provide a sample JWT payload."""
    return {
        'sub': 'user-123',
        'email': 'test@example.com',
        'exp': 9999999999,  # Far future
        'iat': 1234567890,
        'iss': 'https://auth.example.com',
    }


@pytest.fixture
def mock_s3_client():
    """Provide a mock boto3 S3 client."""
    client = MagicMock()
    client.put_object.return_value = {'ETag': '"test-etag"'}
    client.get_object.return_value = {
        'Body': MagicMock(),
        'ContentLength': 1024,
    }
    return client


@pytest.fixture
def temp_jwt_key(tmp_path):
    """Create temporary JWT key files for testing."""
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    
    # Generate RSA key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Write private key
    private_key_path = tmp_path / "private_key.pem"
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    private_key_path.write_bytes(private_key_pem)
    
    # Write public key
    public_key = private_key.public_key()
    public_key_path = tmp_path / "public_key.pem"
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    public_key_path.write_bytes(public_key_pem)
    
    return {
        'private_key_path': str(private_key_path),
        'public_key_path': str(public_key_path),
        'private_key': private_key,
        'public_key': public_key,
    }


@pytest.fixture
def mock_celery_app():
    """Provide a mock Celery app."""
    app = MagicMock()
    app.conf = MagicMock()
    return app


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Reset settings cache between tests."""
    from oxutils.settings import OxUtilsSettings
    yield
    # Clear any cached settings
    if hasattr(OxUtilsSettings, '_instance'):
        delattr(OxUtilsSettings, '_instance')


@pytest.fixture
def mock_structlog_logger():
    """Provide a mock structlog logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.debug = MagicMock()
    return logger
