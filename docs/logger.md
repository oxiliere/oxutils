# Structured Logging

**JSON logs with request tracking using django-structlog**

## Features

- JSON-formatted logs with ISO timestamps
- Automatic request_id tracking for correlation
- Automatic context enrichment (user, domain, service, IP, tenant)
- Dual output: console (human-readable) and JSON file
- Celery task logging support
- Command logging support
- Multitenancy support

## Configuration

### Django Settings

```python
# settings.py
from oxutils.conf import UTILS_APPS, AUDIT_MIDDLEWARE
from oxutils.logger.settings import (
    LOGGING,
    DJANGO_STRUCTLOG_CELERY_ENABLED,
    DJANGO_STRUCTLOG_IP_LOGGING_ENABLED,
    DJANGO_STRUCTLOG_USER_ID_FIELD,
    DJANGO_STRUCTLOG_COMMAND_LOGGING_ENABLED,
)

INSTALLED_APPS = [
    *UTILS_APPS,  # Includes django_structlog
]

MIDDLEWARE = [
    *AUDIT_MIDDLEWARE,  # Includes RequestMiddleware for request_id generation
]

# Import logging configuration
LOGGING = LOGGING
DJANGO_STRUCTLOG_CELERY_ENABLED = DJANGO_STRUCTLOG_CELERY_ENABLED
DJANGO_STRUCTLOG_IP_LOGGING_ENABLED = DJANGO_STRUCTLOG_IP_LOGGING_ENABLED
DJANGO_STRUCTLOG_USER_ID_FIELD = DJANGO_STRUCTLOG_USER_ID_FIELD
DJANGO_STRUCTLOG_COMMAND_LOGGING_ENABLED = DJANGO_STRUCTLOG_COMMAND_LOGGING_ENABLED
```

### Environment Variables

#### Service Identification

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OXI_SERVICE_NAME` | string | `'Oxutils'` | Nom du service qui apparaît dans tous les logs. Permet d'identifier la source des logs dans un environnement multi-services. |
| `OXI_SITE_NAME` | string | `'Oxiliere'` | Nom du site/application. |
| `OXI_SITE_DOMAIN` | string | `'oxiliere.com'` | Domaine principal du site. |

#### Logging Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OXI_LOG_FILE_PATH` | string | `'logs/oxiliere.log'` | Chemin du fichier de logs JSON. Le fichier sera créé automatiquement si le répertoire existe. Utilisé par le handler `json_file`. |

#### Multitenancy

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OXI_MULTITENANCY` | boolean | `False` | Active le support multitenancy. Si `true`, le champ `tenant` (nom du schéma) est automatiquement ajouté à tous les logs via le receiver `bind_domain`. |

#### Example Configuration

```bash
# Service identification
OXI_SERVICE_NAME=my-service
OXI_SITE_NAME=Oxiliere
OXI_SITE_DOMAIN=oxiliere.com

# Log file path
OXI_LOG_FILE_PATH=logs/oxiliere.log

# Multitenancy (optional)
OXI_MULTITENANCY=true
```

## Logging Configuration

The logger uses two handlers:

1. **Console Handler**: Human-readable colored output for development
2. **JSON File Handler**: Structured JSON logs for production/analysis

Two loggers are configured:
- `django_structlog`: For django-structlog internal logs
- `oxiliere_log`: For application logs

## Usage

### Basic Logging

```python
import structlog

logger = structlog.get_logger("oxiliere_log")

# Simple event
logger.info("user_logged_in", user_id=user.id)

# With structured data
logger.info(
    "order_created",
    order_id=order.id,
    total=float(order.total),
    items_count=order.items.count()
)
```

### Error Logging

```python
try:
    process_payment(order)
except PaymentError as e:
    logger.error(
        "payment_failed",
        order_id=order.id,
        error=str(e),
        exc_info=True  # Includes full traceback
    )
```

### Custom Context

```python
# Bind context for all subsequent logs in this execution
structlog.contextvars.bind_contextvars(
    transaction_id=transaction.id,
    payment_method="stripe"
)

logger.info("payment_initiated")
logger.info("payment_completed")

# Clear context when done
structlog.contextvars.clear_contextvars()
```

## Automatic Context Enrichment

The logger automatically adds context to all logs via the `bind_extra_request_metadata` signal receiver:

- **domain**: Current site domain
- **user_id**: Authenticated user ID (as string)
- **service**: Service name from `OXI_SERVICE_NAME`
- **tenant**: Current tenant schema (if multitenancy enabled)
- **ip**: Client IP address
- **request_id**: Unique request identifier

## Log Output Format

### Console Output (Development)

```
2024-12-24T14:03:00Z [info     ] user_logged_in [oxiliere_log] domain=oxiliere.com request_id=abc-123 service=my-service user_id=42
```

### JSON File Output (Production)

```json
{
  "event": "user_logged_in",
  "timestamp": "2024-12-24T14:03:00.123456Z",
  "level": "info",
  "logger": "oxiliere_log",
  "request_id": "abc-def-123-456",
  "ip": "192.168.1.100",
  "domain": "oxiliere.com",
  "service": "my-service",
  "user_id": "42",
  "tenant": "client_schema"
}
```

## Request ID Tracking

### Access Request ID

```python
import structlog

# Get current context including request_id
context = structlog.contextvars.get_contextvars()
request_id = context.get('request_id')

# Or use the utility function
from oxutils.audit.utils import get_request_id
request_id = get_request_id()
```

### Correlation with Audit Logs

The same `request_id` is stored in auditlog entries via the `cid` field:

```python
from auditlog.models import LogEntry

# Find all audit entries for a specific request
entries = LogEntry.objects.filter(cid=request_id)

# Correlate logs with audit trail
for entry in entries:
    logger.info(
        "audit_entry_found",
        model=entry.content_type.model,
        action=entry.action,
        changes=entry.changes
    )
```

## Celery Task Logging

Celery tasks automatically include task context:

```python
from celery import shared_task
import structlog

logger = structlog.get_logger("oxiliere_log")

@shared_task
def process_order(order_id):
    logger.info("task_started", order_id=order_id)
    # Task context (task_id, task_name) automatically added
    logger.info("task_completed", order_id=order_id)
```

## Management Command Logging

Django management commands are automatically logged:

```python
from django.core.management.base import BaseCommand
import structlog

logger = structlog.get_logger("oxiliere_log")

class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("command_started")
        # Command context automatically added
        logger.info("command_completed")
```

## Multitenancy Support

When `OXI_MULTITENANCY=true`, the current tenant schema is automatically added to all logs:

```python
# Automatically includes tenant in context
logger.info("tenant_operation", action="create_invoice")

# Output includes: tenant="client_schema"
```

## Processors Pipeline

The structlog configuration includes:

1. `merge_contextvars`: Merge context variables
2. `filter_by_level`: Filter by log level
3. `TimeStamper`: Add ISO timestamps
4. `add_logger_name`: Add logger name
5. `add_log_level`: Add log level
6. `PositionalArgumentsFormatter`: Format positional args
7. `StackInfoRenderer`: Render stack info
8. `format_exc_info`: Format exceptions
9. `UnicodeDecoder`: Decode unicode
10. `ProcessorFormatter.wrap_for_formatter`: Wrap for output

## Best Practices

1. **Use structured data**: Pass context as keyword arguments, not in the message
2. **Use meaningful event names**: `user_logged_in` not `User logged in`
3. **Include relevant IDs**: Always log entity IDs for traceability
4. **Use appropriate log levels**: INFO for normal operations, ERROR for failures
5. **Include exc_info for errors**: Always use `exc_info=True` when logging exceptions
6. **Bind context for related operations**: Use `bind_contextvars` for transaction-scoped context

## Related Docs

- [Settings](./settings.md) - Service configuration
- [Celery](./celery.md) - Logging in tasks
- [Audit](./audit.md) - Audit trail integration
