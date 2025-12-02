# Celery Integration

**Pre-configured Celery with structured logging**

## Configuration

```python
# settings.py
from oxutils.conf import UTILS_APPS

INSTALLED_APPS = [
    *UTILS_APPS,  # Includes django_celery_results
]

# Celery settings
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'
```

## Usage

```python
# tasks.py
from celery import shared_task
import structlog

logger = structlog.get_logger(__name__)

@shared_task
def process_order(order_id):
    logger.info("processing_order", order_id=order_id)
    
    order = Order.objects.get(id=order_id)
    order.process()
    
    logger.info("order_processed", order_id=order_id)
    return order.id

# Call task
process_order.delay(order_id=123)
```

## Structured Logging in Tasks

Correlation IDs are automatically propagated to Celery tasks:

```python
@shared_task
def send_email(user_id):
    logger = structlog.get_logger(__name__)
    logger.info("sending_email", user_id=user_id)
    # CID automatically included in logs
```

## Related Docs

- [Logger](./logger.md) - Structured logging
- [Settings](./settings.md) - Configuration
