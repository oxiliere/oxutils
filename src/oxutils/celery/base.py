import logging

import structlog
from celery import Celery
from celery.signals import setup_logging
from django.conf import settings
from django_structlog.celery.steps import DjangoStructLogInitStep





celery_app = Celery(getattr(settings, "CELERY_APP_NAME", 'oxiliere_celery'))

celery_app.config_from_object('django.conf:settings', namespace='CELERY')

# A step to initialize django-structlog
celery_app.steps['worker'].add(DjangoStructLogInitStep)

celery_app.autodiscover_tasks()


@setup_logging.connect
def receiver_setup_logging(loglevel, logfile, format, colorize, **kwargs):  # pragma: no cover
    logging.config.dictConfig(
        {
           "version": 1,
           "disable_existing_loggers": False,
           "formatters": {
               "json_formatter": {
                   "()": structlog.stdlib.ProcessorFormatter,
                   "processor": structlog.processors.JSONRenderer(),
               },
               "plain_console": {
                   "()": structlog.stdlib.ProcessorFormatter,
                   "processor": structlog.dev.ConsoleRenderer(),
               },
               "key_value": {
                   "()": structlog.stdlib.ProcessorFormatter,
                   "processor": structlog.processors.KeyValueRenderer(
                        key_order=['timestamp', 'level', 'event', 'logger']
                    ),
               },
           },
           "handlers": {
               "console": {
                   "class": "logging.StreamHandler",
                   "formatter": "plain_console",
                   'filters': ['correlation'],
               },
               "json_file": {
                   "class": "logging.handlers.WatchedFileHandler",
                   "filename": "logs/json.log",
                   "formatter": "json_formatter",
                   'filters': ['correlation'],
               },
               "flat_line_file": {
                   "class": "logging.handlers.WatchedFileHandler",
                   "filename": "logs/flat_line.log",
                   "formatter": "key_value",
                   'filters': ['correlation'],
               },
           },
            'filters': {
                'correlation': {
                    '()': 'cid.log.CidContextFilter'
                },
            },
           "loggers": {
               "django_structlog": {
                   "handlers": ["console", "flat_line_file", "json_file"],
                   "level": "INFO",
               },
               "oxiliere_log": {
                   "handlers": ["console", "flat_line_file", "json_file"],
                   "level": "INFO",
               },
           }
       }
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

