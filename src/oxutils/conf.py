UTILS_APPS = (
    'django_structlog',
    'auditlog',
    'cid.apps.CidAppConfig',
    'django_celery_results',
    'oxutils.audit',
)

AUDIT_MIDDLEWARE = (
    'cid.middleware.CidMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
    'django_structlog.middlewares.RequestMiddleware',
)
