UTILS_APPS = (
    'django_structlog',
    'auditlog',
    'django_celery_results',
    'oxutils.audit',
)

AUDIT_MIDDLEWARE = (
    'django_structlog.middlewares.RequestMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
)
