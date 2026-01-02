"""
Basic OxUtils Setup Example

This example shows how to configure OxUtils in a Django project.
"""

# settings.py
from oxutils.conf import UTILS_APPS, AUDIT_MIDDLEWARE
from oxutils.settings import oxi_settings

# 1. Add OxUtils apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # OxUtils apps
    *UTILS_APPS,
    
    # Your apps
    'myapp',
]

# 2. Add OxUtils middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    
    # OxUtils middleware (early in the stack)
    *AUDIT_MIDDLEWARE,
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 4. Celery configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'

# 5. Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'django_structlog.formatters.JSONFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
