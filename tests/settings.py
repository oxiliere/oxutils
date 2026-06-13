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
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.mfa',
    'django_structlog',
    'auditlog',
    'django_celery_results',
    'cacheops',
    'oxutils.audit',
    'oxutils.currency',
    'oxutils.users',
    'oxutils.permissions',
    'oxutils.auth',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django_structlog.middlewares.RequestMiddleware',
    'allauth.account.middleware.AccountMiddleware',
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
ACCESS_MANAGER_ROLE = 'manager'
ACCESS_MANAGER_CONTEXT = {}
ACCESS_SCOPES = ['access', 'articles', 'users', 'comments']
CACHE_CHECK_PERMISSION = False
FIELD_MASKING_KEY = 'LCPN2bFN2NHA6XCZscpv8JctYJQ2FTfuVKIunFUchnE='

# Django Allauth / Auth settings
SITE_ID = 1
OXI_COOKIE_DOMAIN = 'example.com'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE = True
JWT_ALL_AUTH_MAX_SESSIONS = 4
OLD_PASSWORD_FIELD_ENABLED = True
LOGOUT_ON_PASSWORD_CHANGE = True
PASSWORD_RESET_COOKIE_HTTP_ONLY = True
PASSWORD_RESET_COOKIE_SECURE = False
PASSWORD_RESET_COOKIE_SAME_SITE = 'Lax'
PASSWORD_RESET_COOKIE_MAX_AGE = 3600
MFA_SIGNING_SALT = 'test-mfa-salt'
MFA_SIGNING_TTL = 300
TENANT_MODEL = 'auth.Tenant'
INVITATION_EXPIRY_DAYS = 7
INVITATIONS_MAX_PER_HOUR = 50
ACCOUNT_FRONTEND_URLS = {
    'account_confirm_email': 'https://app.example.com/confirm-email/{key}',
    'account_reset_password': 'https://app.example.com/reset-password/{uid}/{token}',
}
