UTILS_APPS = (
    'django_structlog',
    'auditlog',
    'cid.apps.CidAppConfig',
    'django_celery_results',
)

AUDIT_MIDDLEWARE = (
    'cid.middleware.CidMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
    'django_structlog.middlewares.RequestMiddleware',
)
