# Structured Logging

**JSON logs with correlation IDs using structlog**

## Features

- JSON-formatted logs
- Correlation ID tracking (CID)
- Automatic context (user, domain, service)
- Multiple formatters (JSON, key-value, colored console)

## Configuration

```python
# settings.py
from oxutils.conf import UTILS_APPS, AUDIT_MIDDLEWARE

INSTALLED_APPS = [
    *UTILS_APPS,  # Includes django_structlog, cid
]

MIDDLEWARE = [
    *AUDIT_MIDDLEWARE,  # Includes CID and RequestMiddleware
]
```

## Usage

```python
import structlog

logger = structlog.get_logger(__name__)

# Basic logging
logger.info("user_logged_in", user_id=user_id)

# With context
logger.info(
    "order_created",
    order_id=order.id,
    total=float(order.total),
    user_id=user.id
)

# Error logging
try:
    process_payment()
except Exception as e:
    logger.error(
        "payment_failed",
        error=str(e),
        exc_info=True
    )
```

## Log Output

```json
{
  "event": "user_logged_in",
  "user_id": "123",
  "timestamp": "2024-01-01T10:00:00Z",
  "level": "info",
  "cid": "abc-def-123",
  "service": "my-service"
}
```

## Correlation ID

Automatic correlation ID tracking across requests:

```python
# Automatically added to all logs in the same request
# Access in views
from cid.locals import get_cid

correlation_id = get_cid()
```

## Related Docs

- [Settings](./settings.md) - Service configuration
- [Celery](./celery.md) - Logging in tasks
