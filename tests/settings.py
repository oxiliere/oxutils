"""
Django settings for OxUtils tests.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'test-secret-key-not-for-production'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django_structlog',
    'auditlog',
    'django_celery_results',
    'cacheops',
    'oxutils.audit',
    'oxutils.currency',
    'oxutils.users',
    'oxutils.permissions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django_structlog.middlewares.RequestMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
    'django.middleware.common.CommonMiddleware',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'oxutils_test',
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'TEST': {
            'NAME': 'oxutils_test_db',
        }
    }
}

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

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ROOT_URLCONF = ''

CACHEOPS = {
    "*.*": {'ops': {}, 'timeout': 0}
}

os.environ.setdefault('OXI_SERVICE_NAME', 'test-service')

OXI_SERVICE_NAME = 'test-service'
OXI_LOG_ACCESS = False
OXI_RETENTION_DELAY = 7

# Permissions settings
ACCESS_MANAGER_SCOPE = 'access'
ACCESS_MANAGER_GROUP = 'manager'
ACCESS_MANAGER_CONTEXT = {}
ACCESS_SCOPES = ['access', 'articles', 'users', 'comments']
CACHE_CHECK_PERMISSION = False
FIELD_MASKING_KEY = 'LCPN2bFN2NHA6XCZscpv8JctYJQ2FTfuVKIunFUchnE='
