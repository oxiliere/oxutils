# Structured Logging

**JSON logs with request tracking using django-structlog**

## Features

- JSON-formatted logs
- Automatic request_id tracking for correlation
- Automatic context (user, domain, service, IP)
- Multiple formatters (JSON, console)
- Celery task logging support

## Configuration

```python
# settings.py
from oxutils.conf import UTILS_APPS, AUDIT_MIDDLEWARE

INSTALLED_APPS = [
    *UTILS_APPS,  # Includes django_structlog
]

MIDDLEWARE = [
    *AUDIT_MIDDLEWARE,  # Includes RequestMiddleware for request_id generation
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
  "request_id": "abc-def-123-456",
  "ip": "127.0.0.1",
  "domain": "example.com",
  "service": "my-service"
}
```

## Request ID Tracking

Automatic request_id generation and tracking across requests:

```python
# Automatically added to all logs in the same request
# Access in views
import structlog

# Get current context including request_id
context = structlog.contextvars.get_contextvars()
request_id = context.get('request_id')

# Or use the utility function
from oxutils.audit.utils import get_request_id
request_id = get_request_id()
```

## Request ID in Audit Logs

The same `request_id` is automatically stored in auditlog entries via the `cid` field, allowing you to correlate audit logs with application logs:

```python
from auditlog.models import LogEntry

# Find all audit entries for a specific request
entries = LogEntry.objects.filter(cid=request_id)
```

## Related Docs

- [Settings](./settings.md) - Service configuration
- [Celery](./celery.md) - Logging in tasks
