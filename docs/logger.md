# Structured Logging Documentation

## Overview

OxUtils provides a comprehensive structured logging system built on `structlog` and `django-structlog`. The system offers JSON-formatted logs, correlation ID tracking, automatic request metadata binding, and multiple output formats optimized for both development and production environments.

### Key Features

- **Structured Logging**: JSON-formatted logs with consistent structure
- **Correlation ID Tracking**: Automatic request correlation across services
- **Request Metadata**: Automatic binding of user, domain, and service information
- **Multiple Formatters**: JSON, key-value, and colored console output
- **Celery Integration**: Structured logging for async tasks
- **Context Variables**: Thread-safe context management
- **Production-Ready**: Optimized for log aggregation and analysis

---

## Table of Contents

- [Architecture](#architecture)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Log Formats](#log-formats)
- [Context Management](#context-management)
- [Integration Patterns](#integration-patterns)
- [Best Practices](#best-practices)
- [Log Analysis](#log-analysis)
- [Troubleshooting](#troubleshooting)

---

## Architecture

### Logging Pipeline

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│  RequestMiddleware      │
│  - Generate CID         │
│  - Bind request context │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│  Application Code       │
│  logger.info(...)       │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│  Structlog Processors   │
│  - Add timestamp        │
│  - Add log level        │
│  - Format exception     │
└──────┬──────────────────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ Console  │   │JSON File │   │Key-Value │
│ (colored)│   │(machine) │   │  File    │
└──────────┘   └──────────┘   └──────────┘
```

### Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Settings** | Logger configuration | `oxutils.logger.settings` |
| **Receivers** | Request metadata binding | `oxutils.logger.receivers` |
| **Middleware** | Request/CID middleware | `django_structlog`, `cid` |
| **Processors** | Log processing pipeline | `structlog.processors` |

---

## Installation & Setup

### Prerequisites

Install required dependencies:

```bash
pip install structlog django-structlog django-cid
```

Or with uv:

```bash
uv add structlog django-structlog django-cid
```

### Basic Setup

1. **Add to INSTALLED_APPS:**

```python
# settings.py
from oxutils.conf import UTILS_APPS

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    # ...
    
    # OxUtils apps
    *UTILS_APPS,  # Includes django_structlog, cid, etc.
    
    # Your apps
    'myapp',
]
```

2. **Add middleware:**

```python
# settings.py
from oxutils.conf import AUDIT_MIDDLEWARE

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    
    # OxUtils middleware
    *AUDIT_MIDDLEWARE,  # CID, Auditlog, RequestMiddleware
    
    'django.middleware.common.CommonMiddleware',
    # ... rest of middleware
]
```

3. **Import logging configuration:**

```python
# settings.py
from oxutils.logger.settings import *

# Optional: Override settings
LOGGING['loggers']['myapp'] = {
    'handlers': ['console', 'json_file'],
    'level': 'DEBUG',
}
```

4. **Configure service name:**

```python
# settings.py or .env
OXI_SERVICE_NAME = 'my-service'
```

---

## Configuration

### Django-Structlog Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `DJANGO_STRUCTLOG_CELERY_ENABLED` | `bool` | `True` | Enable Celery task logging |
| `DJANGO_STRUCTLOG_IP_LOGGING_ENABLED` | `bool` | `True` | Log client IP addresses |
| `DJANGO_STRUCTLOG_USER_ID_FIELD` | `str` | `'pk'` | User model field for logging |
| `DJANGO_STRUCTLOG_COMMAND_LOGGING_ENABLED` | `bool` | `True` | Enable management command logging |

### Log Formatters

| Formatter | Output Format | Use Case |
|-----------|---------------|----------|
| `json_formatter` | JSON | Production, log aggregation |
| `plain_console` | Colored console | Development |
| `key_value` | Key-value pairs | Production, human-readable |

### Log Handlers

| Handler | Output | Formatter |
|---------|--------|-----------|
| `console` | stdout | `plain_console` |
| `json_file` | `logs/json.log` | `json_formatter` |
| `flat_line_file` | `logs/flat_line.log` | `key_value` |

### Loggers

| Logger Name | Handlers | Level | Purpose |
|-------------|----------|-------|---------|
| `django_structlog` | console, json_file | INFO | Django-structlog events |
| `oxiliere_log` | console, json_file | INFO | Application logs |

### Structlog Processors

The logging pipeline includes these processors (in order):

1. **`merge_contextvars`** - Merge context variables
2. **`filter_by_level`** - Filter by log level
3. **`TimeStamper`** - Add ISO timestamp
4. **`add_logger_name`** - Add logger name
5. **`add_log_level`** - Add log level
6. **`PositionalArgumentsFormatter`** - Format positional args
7. **`StackInfoRenderer`** - Render stack traces
8. **`format_exc_info`** - Format exceptions
9. **`UnicodeDecoder`** - Decode unicode
10. **`ProcessorFormatter.wrap_for_formatter`** - Prepare for output

---

## Usage Examples

### Basic Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# Info log
logger.info("user_logged_in", user_id=123, username="john")

# Warning log
logger.warning("rate_limit_exceeded", user_id=123, attempts=5)

# Error log
logger.error("payment_failed", order_id="ORD-123", error="Insufficient funds")

# Debug log
logger.debug("cache_hit", key="user:123", ttl=3600)
```

### Logging with Context

```python
import structlog

logger = structlog.get_logger(__name__)

def process_order(order_id: str):
    """Process order with contextual logging."""
    logger.info("order_processing_started", order_id=order_id)
    
    try:
        order = Order.objects.get(id=order_id)
        
        logger.info(
            "order_retrieved",
            order_id=order_id,
            status=order.status,
            total=float(order.total)
        )
        
        # Process order
        result = order.process()
        
        logger.info(
            "order_processed",
            order_id=order_id,
            result=result,
            processing_time=result.duration
        )
        
        return result
        
    except Order.DoesNotExist:
        logger.error("order_not_found", order_id=order_id)
        raise
        
    except Exception as exc:
        logger.error(
            "order_processing_failed",
            order_id=order_id,
            error=str(exc),
            exc_info=True  # Include stack trace
        )
        raise
```

### Exception Logging

```python
import structlog

logger = structlog.get_logger(__name__)

try:
    result = risky_operation()
except ValueError as e:
    logger.error(
        "validation_error",
        error=str(e),
        exc_info=True  # Includes full traceback
    )
except Exception as e:
    logger.exception(
        "unexpected_error",
        operation="risky_operation"
    )  # Automatically includes exc_info
    raise
```

### Performance Logging

```python
import structlog
import time

logger = structlog.get_logger(__name__)

def timed_operation(operation_name: str):
    """Decorator for timing operations."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            logger.info(
                "operation_started",
                operation=operation_name
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    "operation_completed",
                    operation=operation_name,
                    duration_seconds=round(duration, 3),
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    "operation_failed",
                    operation=operation_name,
                    duration_seconds=round(duration, 3),
                    error=str(e),
                    success=False
                )
                raise
        
        return wrapper
    return decorator

# Usage
@timed_operation("database_query")
def fetch_users():
    return User.objects.all()
```

---

## Log Formats

### JSON Format (Production)

```json
{
  "event": "user_logged_in",
  "user_id": 123,
  "username": "john",
  "timestamp": "2024-12-01T15:30:45.123456Z",
  "level": "info",
  "logger": "myapp.views",
  "cid": "550e8400-e29b-41d4-a716-446655440000",
  "domain": "example.com",
  "service": "my-service",
  "request_id": "req-abc123",
  "ip": "192.168.1.1"
}
```

### Key-Value Format (Production)

```
timestamp='2024-12-01T15:30:45.123456Z' level='info' event='user_logged_in' logger='myapp.views' user_id=123 username='john' cid='550e8400-e29b-41d4-a716-446655440000' domain='example.com' service='my-service'
```

### Console Format (Development)

```
2024-12-01 15:30:45 [info     ] user_logged_in                 [myapp.views] user_id=123 username=john cid=550e8400-e29b-41d4-a716-446655440000
```

---

## Context Management

### Binding Context Variables

Context variables are automatically bound to all subsequent log entries in the same request/task.

#### Automatic Binding (via Middleware)

The `bind_domain` receiver automatically binds:

```python
# Automatically bound by middleware
{
    "domain": "example.com",
    "cid": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "123",
    "service": "my-service"
}
```

#### Manual Binding

```python
import structlog

# Bind context for current request/task
structlog.contextvars.bind_contextvars(
    order_id="ORD-123",
    customer_id="CUST-456"
)

# All subsequent logs will include these fields
logger.info("processing_order")  # Includes order_id and customer_id

# Clear specific context
structlog.contextvars.unbind_contextvars("order_id")

# Clear all context
structlog.contextvars.clear_contextvars()
```

#### Temporary Context

```python
import structlog

logger = structlog.get_logger(__name__)

# Bind context temporarily
with structlog.contextvars.bound_contextvars(transaction_id="TXN-789"):
    logger.info("transaction_started")
    # Process transaction
    logger.info("transaction_completed")
# transaction_id is automatically unbound after the block
```

### Context in Views

```python
from django.http import JsonResponse
import structlog

logger = structlog.get_logger(__name__)

def my_view(request):
    """View with contextual logging."""
    # Context is automatically bound by middleware
    # (user_id, domain, cid, service)
    
    # Add view-specific context
    structlog.contextvars.bind_contextvars(
        view="my_view",
        method=request.method
    )
    
    logger.info("view_accessed")
    
    # Process request
    result = process_request(request)
    
    logger.info("view_completed", status=200)
    
    return JsonResponse(result)
```

### Context in Celery Tasks

```python
from celery import shared_task
import structlog

logger = structlog.get_logger(__name__)

@shared_task
def process_payment(payment_id: str):
    """Celery task with context."""
    # Bind task-specific context
    structlog.contextvars.bind_contextvars(
        task="process_payment",
        payment_id=payment_id
    )
    
    logger.info("task_started")
    
    try:
        payment = Payment.objects.get(id=payment_id)
        payment.process()
        
        logger.info("task_completed", success=True)
        
    except Exception as e:
        logger.error("task_failed", error=str(e), exc_info=True)
        raise
```

---

## Integration Patterns

### Django Views

```python
from django.views import View
from django.http import JsonResponse
import structlog

logger = structlog.get_logger(__name__)

class OrderView(View):
    def get(self, request, order_id):
        """Get order with logging."""
        structlog.contextvars.bind_contextvars(
            view="OrderView",
            action="get",
            order_id=order_id
        )
        
        logger.info("fetching_order")
        
        try:
            order = Order.objects.get(id=order_id)
            
            logger.info(
                "order_found",
                status=order.status,
                total=float(order.total)
            )
            
            return JsonResponse(order.to_dict())
            
        except Order.DoesNotExist:
            logger.warning("order_not_found")
            return JsonResponse(
                {'error': 'Order not found'},
                status=404
            )
```

### Django Ninja API

```python
from ninja import Router
import structlog

router = Router()
logger = structlog.get_logger(__name__)

@router.get("/users/{user_id}")
def get_user(request, user_id: str):
    """Get user with structured logging."""
    structlog.contextvars.bind_contextvars(
        endpoint="get_user",
        user_id=user_id
    )
    
    logger.info("api_request")
    
    try:
        user = User.objects.get(id=user_id)
        
        logger.info(
            "user_retrieved",
            username=user.username,
            is_active=user.is_active
        )
        
        return user
        
    except User.DoesNotExist:
        logger.warning("user_not_found")
        raise Http404("User not found")
```

### Service Layer

```python
import structlog
from oxutils.mixins.services import BaseService

logger = structlog.get_logger(__name__)

class OrderService(BaseService):
    logger = logger
    
    def create_order(self, user_id: str, items: list):
        """Create order with comprehensive logging."""
        structlog.contextvars.bind_contextvars(
            service="OrderService",
            action="create_order",
            user_id=user_id,
            item_count=len(items)
        )
        
        logger.info("order_creation_started")
        
        try:
            # Create order
            order = Order.objects.create(user_id=user_id)
            
            logger.info(
                "order_created",
                order_id=str(order.id)
            )
            
            # Add items
            for item in items:
                order.add_item(item)
                logger.debug(
                    "item_added",
                    order_id=str(order.id),
                    item_id=item['id']
                )
            
            logger.info(
                "order_creation_completed",
                order_id=str(order.id),
                total_items=len(items),
                total_amount=float(order.total)
            )
            
            return order
            
        except Exception as exc:
            logger.error(
                "order_creation_failed",
                error=str(exc),
                exc_info=True
            )
            self.exception_handler(exc)
```

### Middleware Logging

```python
import structlog
import time

logger = structlog.get_logger(__name__)

class RequestLoggingMiddleware:
    """Middleware to log all requests."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Log request
        logger.info(
            "request_started",
            method=request.method,
            path=request.path,
            query_params=dict(request.GET)
        )
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            "request_completed",
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            duration_seconds=round(duration, 3)
        )
        
        return response
```

---

## Best Practices

### 1. Use Structured Fields

**❌ Bad - String interpolation:**
```python
logger.info(f"User {user_id} logged in from {ip_address}")
```

**✅ Good - Structured fields:**
```python
logger.info(
    "user_logged_in",
    user_id=user_id,
    ip_address=ip_address
)
```

### 2. Consistent Event Names

Use snake_case and descriptive event names:

```python
# Good event names
logger.info("user_created")
logger.info("payment_processed")
logger.info("order_shipped")
logger.error("database_connection_failed")

# Bad event names
logger.info("User Created")  # Not snake_case
logger.info("done")  # Not descriptive
logger.info("error1")  # Not meaningful
```

### 3. Include Relevant Context

```python
# Minimal context
logger.info("order_created", order_id=order_id)

# Rich context (better for debugging)
logger.info(
    "order_created",
    order_id=order_id,
    user_id=user_id,
    total_amount=float(order.total),
    item_count=order.items.count(),
    payment_method=order.payment_method,
    shipping_address=order.shipping_address
)
```

### 4. Log Levels

Use appropriate log levels:

```python
# DEBUG - Detailed diagnostic information
logger.debug("cache_lookup", key="user:123", hit=True)

# INFO - General informational messages
logger.info("user_logged_in", user_id=123)

# WARNING - Warning messages for potentially harmful situations
logger.warning("rate_limit_approaching", user_id=123, requests=95)

# ERROR - Error events that might still allow the application to continue
logger.error("payment_failed", order_id="ORD-123", error="Card declined")

# CRITICAL - Very severe error events
logger.critical("database_unavailable", error=str(exc))
```

### 5. Exception Logging

```python
# Include exc_info for stack traces
try:
    risky_operation()
except Exception as e:
    logger.error(
        "operation_failed",
        operation="risky_operation",
        error=str(e),
        exc_info=True  # Includes full traceback
    )
    raise

# Or use logger.exception (automatically includes exc_info)
try:
    risky_operation()
except Exception:
    logger.exception("operation_failed")
    raise
```

### 6. Performance Considerations

```python
# Avoid expensive operations in log calls
# ❌ Bad
logger.debug("data", expensive_data=compute_expensive_data())

# ✅ Good - Check level first
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("data", expensive_data=compute_expensive_data())
```

### 7. Sensitive Data

Never log sensitive information:

```python
# ❌ Bad - Logs sensitive data
logger.info(
    "user_authenticated",
    username=username,
    password=password  # NEVER log passwords!
)

# ✅ Good - Mask or exclude sensitive data
logger.info(
    "user_authenticated",
    username=username,
    auth_method="password"
)
```

---

## Log Analysis

### Querying JSON Logs

#### Using jq

```bash
# Get all error logs
cat logs/json.log | jq 'select(.level == "error")'

# Get logs for specific user
cat logs/json.log | jq 'select(.user_id == "123")'

# Get logs with specific event
cat logs/json.log | jq 'select(.event == "order_created")'

# Count events by type
cat logs/json.log | jq -r '.event' | sort | uniq -c | sort -rn

# Get average duration for an operation
cat logs/json.log | jq -r 'select(.event == "operation_completed") | .duration_seconds' | awk '{sum+=$1; count++} END {print sum/count}'
```

#### Using Python

```python
import json

def analyze_logs(log_file: str):
    """Analyze JSON log file."""
    events = {}
    errors = []
    
    with open(log_file, 'r') as f:
        for line in f:
            try:
                log = json.loads(line)
                
                # Count events
                event = log.get('event', 'unknown')
                events[event] = events.get(event, 0) + 1
                
                # Collect errors
                if log.get('level') == 'error':
                    errors.append(log)
                    
            except json.JSONDecodeError:
                continue
    
    return {
        'total_events': sum(events.values()),
        'event_counts': events,
        'error_count': len(errors),
        'errors': errors
    }

# Usage
stats = analyze_logs('logs/json.log')
print(f"Total events: {stats['total_events']}")
print(f"Errors: {stats['error_count']}")
```

### ELK Stack Integration

```python
# Logstash configuration for JSON logs
input {
  file {
    path => "/path/to/logs/json.log"
    codec => "json"
    type => "django-app"
  }
}

filter {
  # Add geoip for IP addresses
  if [ip] {
    geoip {
      source => "ip"
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "django-logs-%{+YYYY.MM.dd}"
  }
}
```

### Correlation ID Tracking

Track requests across services using correlation IDs:

```python
# Service A
logger.info("request_sent_to_service_b", cid=cid, target="service-b")

# Service B (receives same CID)
logger.info("request_received_from_service_a", cid=cid, source="service-a")

# Query logs by CID
cat logs/json.log | jq 'select(.cid == "550e8400-e29b-41d4-a716-446655440000")'
```

---

## Troubleshooting

### Common Issues

#### 1. Logs Not Appearing

**Check log level:**
```python
# settings.py
LOGGING['loggers']['myapp']['level'] = 'DEBUG'
```

**Verify logger name:**
```python
import structlog

# Use correct logger name
logger = structlog.get_logger(__name__)  # ✅
logger = structlog.get_logger('myapp')   # ✅
```

#### 2. Missing Context Variables

**Ensure middleware is installed:**
```python
MIDDLEWARE = [
    'cid.middleware.CidMiddleware',  # Must be early
    'django_structlog.middlewares.RequestMiddleware',
    # ...
]
```

**Check signal receiver:**
```python
# Ensure receiver is imported
# In apps.py
def ready(self):
    import oxutils.logger.receivers
```

#### 3. JSON Parsing Errors

**Ensure proper JSON formatting:**
```python
# Use json_formatter for JSON output
LOGGING['handlers']['json_file']['formatter'] = 'json_formatter'
```

#### 4. Log File Not Created

**Check directory exists:**
```bash
mkdir -p logs
chmod 755 logs
```

**Verify file path:**
```python
LOGGING['handlers']['json_file']['filename'] = 'logs/json.log'
```

### Debugging

**Enable debug logging:**
```python
import logging

logging.basicConfig(level=logging.DEBUG)
structlog_logger = logging.getLogger('structlog')
structlog_logger.setLevel(logging.DEBUG)
```

**Test logging configuration:**
```python
import structlog

logger = structlog.get_logger(__name__)

# Test all log levels
logger.debug("debug_message", test=True)
logger.info("info_message", test=True)
logger.warning("warning_message", test=True)
logger.error("error_message", test=True)
```

---

## Testing

### Unit Tests

```python
import pytest
import structlog
from structlog.testing import LogCapture

@pytest.fixture
def log_output():
    """Capture log output for testing."""
    return LogCapture()

@pytest.fixture(autouse=True)
def configure_structlog(log_output):
    """Configure structlog for testing."""
    structlog.configure(
        processors=[log_output],
        logger_factory=structlog.ReturnLoggerFactory(),
    )

def test_logging(log_output):
    """Test logging output."""
    logger = structlog.get_logger()
    
    logger.info("test_event", user_id=123)
    
    assert log_output.entries == [
        {
            'event': 'test_event',
            'user_id': 123,
            'log_level': 'info'
        }
    ]
```

### Integration Tests

```python
from django.test import TestCase
import structlog

class LoggingTestCase(TestCase):
    def test_request_logging(self):
        """Test request logging."""
        response = self.client.get('/api/test')
        
        # Verify logs were created
        # (Check log file or use log capture)
        self.assertEqual(response.status_code, 200)
```

---

## Related Documentation

- [Celery Integration](./celery.md) - Celery logging integration
- [Audit System](./audit.md) - Audit logging and tracking
- [Settings & Configuration](./settings.md) - Logger configuration

---

## Support

For questions or issues regarding structured logging, please contact the Oxiliere development team or open an issue in the repository.
