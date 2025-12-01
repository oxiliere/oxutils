# Celery Integration Documentation

## Overview

OxUtils provides a pre-configured Celery application with structured logging, correlation ID tracking, and Django integration. The setup includes automatic task discovery, comprehensive logging with multiple formatters, and best practices for distributed task processing in the Oxiliere ecosystem.

### Key Features

- **Pre-configured Celery App**: Ready-to-use Celery instance with Django integration
- **Structured Logging**: Integration with `structlog` and `django-structlog`
- **Correlation ID Tracking**: Automatic request correlation across tasks
- **Multiple Log Formats**: JSON, key-value, and console formatters
- **Auto-discovery**: Automatic task discovery from all installed apps
- **Production-Ready**: Optimized settings for production environments

---

## Table of Contents

- [Installation & Setup](#installation--setup)
- [Celery Application](#celery-application)
- [Creating Tasks](#creating-tasks)
- [Task Patterns](#task-patterns)
- [Logging](#logging)
- [Configuration](#configuration)
- [Scheduling](#scheduling)
- [Monitoring](#monitoring)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Installation & Setup

### Prerequisites

Install required dependencies:

```bash
pip install celery redis django-celery-beat django-structlog
```

Or with uv:

```bash
uv add celery redis django-celery-beat django-structlog
```

### Basic Configuration

1. **Import Celery settings in your Django settings:**

```python
# settings.py
from oxutils.celery.settings import *
from oxutils.logger.settings import *

# Celery Configuration
CELERY_APP_NAME = 'myproject'
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Optional: Configure task routing
CELERY_TASK_ROUTES = {
    'myapp.tasks.heavy_task': {'queue': 'heavy'},
    'myapp.tasks.light_task': {'queue': 'light'},
}

# Optional: Configure task time limits
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes
```

2. **Create Celery app in your project:**

```python
# myproject/celery.py
from oxutils.celery import celery_app

__all__ = ('celery_app',)
```

3. **Initialize Celery in your Django app:**

```python
# myproject/__init__.py
from .celery import celery_app

__all__ = ('celery_app',)
```

### Running Workers

```bash
# Development - single worker
celery -A myproject worker --loglevel=info

# Production - multiple workers with concurrency
celery -A myproject worker --loglevel=info --concurrency=4

# With specific queues
celery -A myproject worker -Q default,heavy,light --loglevel=info

# With autoscaling
celery -A myproject worker --autoscale=10,3 --loglevel=info
```

### Running Beat Scheduler

```bash
# For periodic tasks
celery -A myproject beat --loglevel=info

# With scheduler database
celery -A myproject beat --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## Celery Application

### Pre-configured Instance

OxUtils provides a pre-configured Celery application with optimal settings.

**Location:** `oxutils.celery.celery_app`

#### Features

| Feature | Description |
|---------|-------------|
| **Django Integration** | Automatic Django settings loading with `CELERY_` namespace |
| **Auto-discovery** | Automatically discovers tasks from all installed apps |
| **Structured Logging** | Integration with structlog and django-structlog |
| **Correlation IDs** | Automatic correlation ID tracking across tasks |
| **Multiple Formatters** | JSON, key-value, and console log formatters |

#### Usage

```python
from oxutils.celery import celery_app

# The app is ready to use
@celery_app.task
def my_task():
    return "Hello from Celery!"
```

---

## Creating Tasks

### Basic Task

```python
# myapp/tasks.py
from celery import shared_task
import structlog

logger = structlog.get_logger(__name__)

@shared_task
def send_email(to: str, subject: str, body: str):
    """Send an email asynchronously."""
    logger.info("sending_email", to=to, subject=subject)
    
    # Your email sending logic here
    send_mail(subject, body, 'from@example.com', [to])
    
    logger.info("email_sent", to=to)
    return f"Email sent to {to}"
```

### Task with Retry

```python
from celery import shared_task
from requests.exceptions import RequestException
import structlog

logger = structlog.get_logger(__name__)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60  # 1 minute
)
def fetch_external_data(self, url: str):
    """Fetch data from external API with retry."""
    try:
        logger.info("fetching_data", url=url)
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
        
    except RequestException as exc:
        logger.warning(
            "fetch_failed",
            url=url,
            error=str(exc),
            retry_count=self.request.retries
        )
        raise self.retry(exc=exc)
```

### Task with Custom Options

```python
@shared_task(
    name='myapp.process_order',
    bind=True,
    max_retries=5,
    default_retry_delay=300,  # 5 minutes
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=3600,  # 1 hour
    retry_jitter=True,
    time_limit=600,  # 10 minutes hard limit
    soft_time_limit=540,  # 9 minutes soft limit
)
def process_order(self, order_id: str):
    """Process an order with comprehensive retry logic."""
    logger.info("processing_order", order_id=order_id)
    
    # Your processing logic
    order = Order.objects.get(id=order_id)
    order.process()
    
    logger.info("order_processed", order_id=order_id)
    return order_id
```

---

## Task Patterns

### Chain Tasks

Execute tasks sequentially, passing results between them.

```python
from celery import chain

# Define tasks
@shared_task
def fetch_data(url: str):
    return requests.get(url).json()

@shared_task
def process_data(data: dict):
    processed = transform(data)
    return processed

@shared_task
def save_data(data: dict):
    Model.objects.create(**data)
    return "saved"

# Chain execution
workflow = chain(
    fetch_data.s('https://api.example.com/data'),
    process_data.s(),
    save_data.s()
)
result = workflow.apply_async()
```

### Group Tasks

Execute tasks in parallel.

```python
from celery import group

@shared_task
def process_item(item_id: str):
    item = Item.objects.get(id=item_id)
    item.process()
    return item_id

# Process multiple items in parallel
item_ids = ['id1', 'id2', 'id3', 'id4', 'id5']
job = group(process_item.s(item_id) for item_id in item_ids)
result = job.apply_async()

# Wait for all tasks to complete
results = result.get()
```

### Chord Tasks

Execute tasks in parallel, then run a callback with all results.

```python
from celery import chord

@shared_task
def fetch_user_data(user_id: str):
    return User.objects.get(id=user_id).to_dict()

@shared_task
def aggregate_results(results: list):
    """Callback that receives all results."""
    logger.info("aggregating_results", count=len(results))
    return {
        'total_users': len(results),
        'users': results
    }

# Execute
user_ids = ['user1', 'user2', 'user3']
callback = chord(
    (fetch_user_data.s(uid) for uid in user_ids),
    aggregate_results.s()
)
result = callback.apply_async()
```

### Periodic Tasks

```python
from celery import shared_task
from celery.schedules import crontab

@shared_task
def cleanup_old_data():
    """Clean up old data daily."""
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted = OldModel.objects.filter(created_at__lt=cutoff_date).delete()
    logger.info("cleanup_completed", deleted_count=deleted[0])
    return deleted[0]

# Configure in settings.py
CELERY_BEAT_SCHEDULE = {
    'cleanup-old-data': {
        'task': 'myapp.tasks.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}
```

### Task with Progress Tracking

```python
from celery import shared_task
from celery_progress.backend import ProgressRecorder

@shared_task(bind=True)
def long_running_task(self, items: list):
    """Task with progress tracking."""
    progress_recorder = ProgressRecorder(self)
    total = len(items)
    
    for i, item in enumerate(items):
        # Process item
        process_item(item)
        
        # Update progress
        progress_recorder.set_progress(
            i + 1,
            total,
            description=f"Processing item {i + 1} of {total}"
        )
    
    return "Completed"
```

---

## Logging

### Structured Logging

OxUtils Celery integration includes comprehensive structured logging.

#### Log Formatters

| Formatter | Output | Use Case |
|-----------|--------|----------|
| `json_formatter` | JSON format | Production, log aggregation |
| `key_value` | Key-value pairs | Production, human-readable |
| `plain_console` | Colored console | Development |

#### Log Files

| File | Format | Purpose |
|------|--------|---------|
| `logs/json.log` | JSON | Machine-readable logs for parsing |
| `logs/flat_line.log` | Key-value | Human-readable production logs |
| Console | Colored | Development debugging |

#### Using Structured Logging

```python
import structlog

logger = structlog.get_logger(__name__)

@shared_task
def process_payment(payment_id: str, amount: float):
    """Process payment with structured logging."""
    
    # Log with context
    logger.info(
        "payment_processing_started",
        payment_id=payment_id,
        amount=amount
    )
    
    try:
        payment = Payment.objects.get(id=payment_id)
        
        logger.info(
            "payment_retrieved",
            payment_id=payment_id,
            status=payment.status
        )
        
        # Process payment
        result = payment.process()
        
        logger.info(
            "payment_processed",
            payment_id=payment_id,
            result=result,
            new_status=payment.status
        )
        
        return result
        
    except Payment.DoesNotExist:
        logger.error(
            "payment_not_found",
            payment_id=payment_id
        )
        raise
        
    except Exception as exc:
        logger.error(
            "payment_processing_failed",
            payment_id=payment_id,
            error=str(exc),
            exc_info=True
        )
        raise
```

#### Correlation ID Tracking

Correlation IDs are automatically tracked across tasks:

```python
@shared_task
def parent_task(data: dict):
    """Parent task that spawns child tasks."""
    logger.info("parent_task_started", data=data)
    
    # Correlation ID is automatically passed to child tasks
    child_task.delay(data['item_id'])
    
    logger.info("parent_task_completed")

@shared_task
def child_task(item_id: str):
    """Child task - correlation ID is preserved."""
    logger.info("child_task_started", item_id=item_id)
    # Logs will have the same correlation ID as parent
```

---

## Configuration

### Essential Settings

```python
# settings.py

# Celery Application Name
CELERY_APP_NAME = 'myproject'

# Broker and Backend
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Task Serialization
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

# Timezone
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Task Result Settings
CELERY_RESULT_EXPIRES = 3600  # 1 hour
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SEND_SENT_EVENT = True

# Worker Settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Task Time Limits
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes

# Cache Backend
CELERY_CACHE_BACKEND = 'default'
```

### Advanced Configuration

```python
# Task Routing
CELERY_TASK_ROUTES = {
    'myapp.tasks.heavy_*': {'queue': 'heavy'},
    'myapp.tasks.light_*': {'queue': 'light'},
    'myapp.tasks.priority_*': {'queue': 'priority'},
}

# Queue Priority
CELERY_TASK_QUEUE_MAX_PRIORITY = 10
CELERY_TASK_DEFAULT_PRIORITY = 5

# Task Compression
CELERY_TASK_COMPRESSION = 'gzip'
CELERY_RESULT_COMPRESSION = 'gzip'

# Task Acknowledgment
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Rate Limiting
CELERY_TASK_ANNOTATIONS = {
    'myapp.tasks.api_call': {'rate_limit': '10/m'},
    'myapp.tasks.email_send': {'rate_limit': '100/h'},
}

# Retry Configuration
CELERY_TASK_AUTORETRY_FOR = (Exception,)
CELERY_TASK_RETRY_BACKOFF = True
CELERY_TASK_RETRY_BACKOFF_MAX = 600  # 10 minutes
CELERY_TASK_RETRY_JITTER = True
```

### Logging Configuration

```python
# Structured Logging
DJANGO_STRUCTLOG_CELERY_ENABLED = True
DJANGO_STRUCTLOG_IP_LOGGING_ENABLED = True
DJANGO_STRUCTLOG_USER_ID_FIELD = 'pk'
DJANGO_STRUCTLOG_COMMAND_LOGGING_ENABLED = True

# Correlation ID
CID_GENERATE = True
CID_HEADER = 'X-Correlation-ID'
```

---

## Scheduling

### Using Celery Beat

#### Database-backed Schedule

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'django_celery_beat',
]

# Use database scheduler
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

#### Define Periodic Tasks

```python
# settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Every minute
    'check-status-every-minute': {
        'task': 'myapp.tasks.check_status',
        'schedule': 60.0,
    },
    
    # Every hour
    'cleanup-hourly': {
        'task': 'myapp.tasks.cleanup',
        'schedule': crontab(minute=0),
    },
    
    # Daily at 2 AM
    'daily-report': {
        'task': 'myapp.tasks.generate_daily_report',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # Weekly on Monday at 8 AM
    'weekly-summary': {
        'task': 'myapp.tasks.weekly_summary',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),
    },
    
    # Monthly on 1st at midnight
    'monthly-billing': {
        'task': 'myapp.tasks.process_monthly_billing',
        'schedule': crontab(hour=0, minute=0, day_of_month=1),
    },
    
    # Every 5 minutes with args
    'sync-data': {
        'task': 'myapp.tasks.sync_external_data',
        'schedule': 300.0,
        'args': ('api_endpoint',),
        'kwargs': {'force': False},
    },
}
```

#### Dynamic Scheduling

```python
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

# Create an interval schedule
schedule, created = IntervalSchedule.objects.get_or_create(
    every=10,
    period=IntervalSchedule.MINUTES,
)

# Create periodic task
PeriodicTask.objects.create(
    interval=schedule,
    name='Dynamic Task',
    task='myapp.tasks.dynamic_task',
    args=json.dumps(['arg1', 'arg2']),
    kwargs=json.dumps({'key': 'value'}),
)
```

---

## Monitoring

### Task Status Checking

```python
from celery.result import AsyncResult

# Get task result
result = AsyncResult(task_id)

# Check status
if result.ready():
    print("Task completed")
    print(f"Result: {result.get()}")
elif result.failed():
    print("Task failed")
    print(f"Error: {result.info}")
else:
    print(f"Task status: {result.state}")
```

### Monitoring with Flower

```bash
# Install Flower
pip install flower

# Run Flower
celery -A myproject flower --port=5555

# Access dashboard at http://localhost:5555
```

### Custom Monitoring

```python
from celery import shared_task
from oxutils.celery import celery_app
import structlog

logger = structlog.get_logger(__name__)

@shared_task
def monitor_task_health():
    """Monitor Celery task health."""
    stats = celery_app.control.inspect().stats()
    active = celery_app.control.inspect().active()
    
    logger.info(
        "celery_health_check",
        workers=len(stats) if stats else 0,
        active_tasks=sum(len(tasks) for tasks in active.values()) if active else 0
    )
    
    return {
        'workers': stats,
        'active_tasks': active
    }
```

### Task Events

```python
from celery import signals

@signals.task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Log when task starts."""
    logger.info(
        "task_started",
        task_id=task_id,
        task_name=task.name
    )

@signals.task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Log when task completes."""
    logger.info(
        "task_completed",
        task_id=task_id,
        task_name=task.name
    )

@signals.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Log when task fails."""
    logger.error(
        "task_failed",
        task_id=task_id,
        task_name=sender.name,
        error=str(exception)
    )
```

---

## Best Practices

### 1. Task Design

**Keep tasks idempotent:**

```python
@shared_task
def process_order(order_id: str):
    """Idempotent order processing."""
    order = Order.objects.get(id=order_id)
    
    # Check if already processed
    if order.status == 'processed':
        logger.info("order_already_processed", order_id=order_id)
        return order_id
    
    # Process order
    order.process()
    return order_id
```

**Use atomic operations:**

```python
from django.db import transaction

@shared_task
def update_inventory(product_id: str, quantity: int):
    """Update inventory atomically."""
    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=product_id)
        product.stock -= quantity
        product.save()
```

### 2. Error Handling

**Comprehensive error handling:**

```python
@shared_task(bind=True, max_retries=3)
def robust_task(self, data: dict):
    """Task with comprehensive error handling."""
    try:
        # Your logic here
        result = process_data(data)
        return result
        
    except TemporaryError as exc:
        # Retry on temporary errors
        logger.warning("temporary_error", error=str(exc))
        raise self.retry(exc=exc, countdown=60)
        
    except PermanentError as exc:
        # Don't retry on permanent errors
        logger.error("permanent_error", error=str(exc))
        raise
        
    except Exception as exc:
        # Log and retry unexpected errors
        logger.error("unexpected_error", error=str(exc), exc_info=True)
        raise self.retry(exc=exc)
```

### 3. Resource Management

**Limit concurrent tasks:**

```python
@shared_task(rate_limit='10/m')
def api_call(endpoint: str):
    """Rate-limited API call."""
    return requests.get(endpoint).json()
```

**Use connection pooling:**

```python
from redis import ConnectionPool

pool = ConnectionPool(host='localhost', port=6379, db=0)

@shared_task
def cache_operation(key: str, value: str):
    """Use connection pool for Redis operations."""
    redis_client = redis.Redis(connection_pool=pool)
    redis_client.set(key, value)
```

### 4. Task Organization

**Organize tasks by module:**

```
myapp/
├── tasks/
│   ├── __init__.py
│   ├── email.py      # Email-related tasks
│   ├── reports.py    # Report generation tasks
│   ├── cleanup.py    # Cleanup tasks
│   └── sync.py       # Data synchronization tasks
```

### 5. Testing

**Test tasks synchronously:**

```python
# tests.py
from myapp.tasks import send_email

def test_send_email():
    """Test email task."""
    # Run task synchronously
    result = send_email.apply(args=['test@example.com', 'Subject', 'Body'])
    
    assert result.successful()
    assert 'sent' in result.result.lower()
```

**Mock external dependencies:**

```python
from unittest.mock import patch

def test_api_task():
    """Test API task with mocked requests."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {'data': 'test'}
        
        result = fetch_external_data.apply(args=['http://api.example.com'])
        assert result.result == {'data': 'test'}
```

---

## Troubleshooting

### Common Issues

#### Tasks Not Executing

**Check worker is running:**

```bash
celery -A myproject inspect active
celery -A myproject inspect registered
```

**Check broker connection:**

```python
from oxutils.celery import celery_app

# Test connection
celery_app.connection().ensure_connection(max_retries=3)
```

#### Tasks Timing Out

**Increase time limits:**

```python
@shared_task(
    time_limit=600,  # 10 minutes
    soft_time_limit=540  # 9 minutes
)
def long_task():
    pass
```

#### Memory Issues

**Reduce prefetch multiplier:**

```python
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
```

**Limit tasks per child:**

```python
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
```

#### Task Results Not Persisting

**Check result backend:**

```python
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_RESULT_EXPIRES = 3600
```

### Debugging

**Enable debug logging:**

```bash
celery -A myproject worker --loglevel=debug
```

**Inspect task details:**

```python
from celery.result import AsyncResult

result = AsyncResult(task_id)
print(f"State: {result.state}")
print(f"Info: {result.info}")
print(f"Traceback: {result.traceback}")
```

---

## Production Deployment

### Supervisor Configuration

```ini
[program:celery_worker]
command=/path/to/venv/bin/celery -A myproject worker --loglevel=info --concurrency=4
directory=/path/to/project
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker_error.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
priority=998

[program:celery_beat]
command=/path/to/venv/bin/celery -A myproject beat --loglevel=info
directory=/path/to/project
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat_error.log
autostart=true
autorestart=true
priority=999
```

### Systemd Service

```ini
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/celery -A myproject worker --loglevel=info --concurrency=4 --pidfile=/var/run/celery/worker.pid
ExecStop=/path/to/venv/bin/celery -A myproject control shutdown
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Related Documentation

- [Audit System](./audit.md) - Audit log export tasks
- [Structured Logging](./logger.md) - Structured logging setup
- [Settings & Configuration](./settings.md) - Celery configuration

---

## Support

For questions or issues regarding Celery integration, please contact the Oxiliere development team or open an issue in the repository.
