"""
Django settings for OxUtils tests.
"""
import os

# Build paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set required environment variables for S3 storage (used by audit models)
os.environ.setdefault('OXI_SERVICE_NAME', 'test-service')
os.environ.setdefault('OXI_USE_LOG_S3', 'True')
os.environ.setdefault('OXI_USE_PRIVATE_S3', 'True')
os.environ.setdefault('OXI_USE_PRIVATE_S3_AS_LOG', 'True')
os.environ.setdefault('OXI_PRIVATE_S3_STORAGE_BUCKET_NAME', 'test-bucket')
os.environ.setdefault('OXI_PRIVATE_S3_ACCESS_KEY_ID', 'test-key')
os.environ.setdefault('OXI_PRIVATE_S3_SECRET_ACCESS_KEY', 'test-secret')
os.environ.setdefault('OXI_PRIVATE_S3_CUSTOM_DOMAIN', 'test.example.com')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'test-secret-key-not-for-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django_structlog',
    'auditlog',
    'cid.apps.CidAppConfig',
    'django_celery_results',
    'oxutils.audit',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'cid.middleware.CidMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
    'django_structlog.middlewares.RequestMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = ''

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
            ],
        },
    },
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = []

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# OxUtils settings for tests
OXI_SERVICE_NAME = 'test-service'
OXI_LOG_ACCESS = False
OXI_RETENTION_DELAY = 7
