# Currency Module

**Multi-source currency exchange rate management with automatic fallback**

## Features

- Automatic currency rate synchronization from multiple sources
- BCC Bank (primary) and OpenExchangeRates (fallback) support
- Historical rate tracking with state management
- REST API endpoints for rate queries
- Admin interface for rate monitoring
- Support for 17 major currencies

## Supported Currencies

```python
AVAILABLES_CURRENCIES = [
    "AOA",  # Angolan Kwanza
    "AUD",  # Australian Dollar
    "BIF",  # Burundian Franc
    "CAD",  # Canadian Dollar
    "CHF",  # Swiss Franc
    "CNY",  # Chinese Yuan
    "EUR",  # Euro
    "GBP",  # British Pound
    "JPY",  # Japanese Yen
    "RWF",  # Rwandan Franc
    "TZS",  # Tanzanian Shilling
    "UGX",  # Ugandan Shilling
    "USD",  # US Dollar
    "XAF",  # Central African CFA Franc
    "XDR",  # Special Drawing Rights
    "ZAR",  # South African Rand
    "ZMW"   # Zambian Kwacha
]
```

## Setup

### Installation

Add to your Django settings:

```python
# settings.py
from oxutils.conf import UTILS_APPS

INSTALLED_APPS = [
    *UTILS_APPS,  # Includes 'oxutils.currency'
    # your apps...
]

# Optional: Enable fallback to OpenExchangeRates if BCC fails
OXI_BCC_FALLBACK_ON_OXR = True
```

### Run Migrations

```bash
python manage.py migrate currency
```

## Usage

### Synchronizing Rates

#### Manual Sync

```python
from oxutils.currency.models import CurrencyState

# Sync rates from BCC (with OXR fallback if configured)
state = CurrencyState.sync()

print(f"Synced {state.currencies.count()} currencies from {state.source}")
```

#### Scheduled Sync (Celery)

```python
# tasks.py
from celery import shared_task
from oxutils.currency.models import CurrencyState

@shared_task
def sync_currency_rates():
    """Sync currency rates daily"""
    try:
        state = CurrencyState.sync()
        return f"Synced {state.currencies.count()} rates"
    except Exception as e:
        return f"Failed to sync rates: {str(e)}"

# celery beat schedule
CELERY_BEAT_SCHEDULE = {
    'sync-currency-rates': {
        'task': 'myapp.tasks.sync_currency_rates',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
}
```

### Querying Rates

#### Get Latest Rates

```python
from oxutils.currency.models import CurrencyState

# Get the most recent currency state
state = CurrencyState.objects.latest()

# Access all currencies
for currency in state.currencies.all():
    print(f"{currency.code}: {currency.rate}")

# Get specific currency
usd_rate = state.currencies.get(code='USD')
print(f"USD Rate: {usd_rate.rate}")
```

#### Get Rate by Code

```python
from oxutils.currency.models import CurrencyState

state = CurrencyState.objects.latest()
eur_currency = state.currencies.get(code='EUR')

# Convert amount
amount_in_usd = 100
amount_in_eur = amount_in_usd * float(eur_currency.rate)
```

### Using the Utils

```python
from oxutils.currency.utils import load_rates, update_rates
from oxutils.currency.schemas import CurrencyStateDetailSchema

# Load rates from external source
rates, source = load_rates()
print(f"Loaded {len(rates)} rates from {source}")

# Update rates from schema (useful for distributed systems)
state_schema = CurrencyStateDetailSchema(
    id=uuid.uuid4(),
    source='BCC',
    currencies={'USD': 1.0, 'EUR': 0.85},
    created_at=datetime.now(),
    updated_at=datetime.now()
)
update_rates(state_schema)
```

## REST API Endpoints

The currency module provides REST API endpoints via Django Ninja:

### Register Controllers

```python
# urls.py
from ninja_extra import NinjaExtraAPI
from oxutils.currency.controllers import CurrencyController

api = NinjaExtraAPI()
api.register_controllers(CurrencyController)
```

### Available Endpoints

#### List Currency States

```http
GET /api/currency/states
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "source": "BCC",
      "created_at": "2025-12-21T10:00:00Z",
      "updated_at": "2025-12-21T10:00:00Z"
    }
  ],
  "count": 1,
  "page": 1,
  "page_size": 20
}
```

#### Get Latest State with Rates

```http
GET /api/currency/states/latest
```

**Response:**
```json
{
  "id": "uuid",
  "source": "BCC",
  "created_at": "2025-12-21T10:00:00Z",
  "updated_at": "2025-12-21T10:00:00Z",
  "currencies": {
    "USD": 1.0,
    "EUR": 0.85,
    "GBP": 0.73,
    "XAF": 655.957
  }
}
```

#### Get Specific State

```http
GET /api/currency/states/{state_id}
```

#### Get Current Rates Only

```http
GET /api/currency/rates
```

**Response:**
```json
{
  "USD": 1.0,
  "EUR": 0.85,
  "GBP": 0.73,
  "XAF": 655.957
}
```

#### Get Rate for Specific Currency

```http
GET /api/currency/rates/EUR
```

**Response:**
```json
{
  "EUR": 0.85
}
```

## Models

### CurrencyState

Represents a snapshot of currency rates at a specific time.

**Fields:**
- `id` (UUID): Primary key
- `source` (CharField): Source of rates (BCC or OXR)
- `created_at` (DateTimeField): When the state was created
- `updated_at` (DateTimeField): Last update time

**Methods:**
- `sync()`: Class method to fetch and save new rates

**Manager Methods:**
- `latest()`: Get the most recent currency state with prefetched currencies

### Currency

Individual currency rate within a state.

**Fields:**
- `id` (UUID): Primary key
- `code` (CharField): Currency code (e.g., 'USD', 'EUR')
- `rate` (DecimalField): Exchange rate (max_digits=10, decimal_places=4)
- `state` (ForeignKey): Related CurrencyState

**Validation:**
- Currency code must be in `AVAILABLES_CURRENCIES`
- Rate must be greater than 0

## Admin Interface

The currency module includes a comprehensive Django admin interface:

### CurrencyState Admin

- View all currency states with source and date
- Inline display of all currencies in a state
- Read-only to prevent accidental modifications
- Filter by source and creation date
- Search by ID and source

### Currency Admin

- View individual currency records
- Filter by code, source, and date
- Search by code and state ID
- Read-only to maintain data integrity

## Configuration

### Settings

```python
# settings.py

# Enable fallback to OpenExchangeRates if BCC fails
OXI_BCC_FALLBACK_ON_OXR = True  # Default: False

# Configure bcc-rates library (if needed)
BCC_RATES_CACHE_DIR = '/path/to/cache'  # Optional
```

## Error Handling

### Sync Failures

```python
from oxutils.currency.models import CurrencyState

try:
    state = CurrencyState.sync()
except ValueError as e:
    # No rates found from any source
    print(f"Sync failed: {e}")
except Exception as e:
    # Other errors (network, parsing, etc.)
    print(f"Unexpected error: {e}")
```

### API Errors

The API returns appropriate HTTP status codes:
- `404`: Currency state or rate not found
- `500`: Internal server error during sync

## Best Practices

1. **Schedule Regular Syncs**: Use Celery Beat to sync rates daily
2. **Monitor Sync Status**: Check logs for sync failures
3. **Use Latest State**: Always query `CurrencyState.objects.latest()` for current rates
4. **Handle Missing Rates**: Always check if a currency exists before accessing
5. **Cache Rates**: Consider caching frequently accessed rates in Redis
6. **Backup States**: Keep historical states for auditing and analysis

## Example: Currency Converter

```python
from oxutils.currency.models import CurrencyState
from decimal import Decimal

class CurrencyConverter:
    def __init__(self):
        self.state = CurrencyState.objects.latest()
        self.rates = {
            c.code: c.rate 
            for c in self.state.currencies.all()
        }
    
    def convert(self, amount: Decimal, from_code: str, to_code: str) -> Decimal:
        """Convert amount from one currency to another"""
        if from_code not in self.rates:
            raise ValueError(f"Currency {from_code} not found")
        if to_code not in self.rates:
            raise ValueError(f"Currency {to_code} not found")
        
        # Convert to base currency (usually USD)
        base_amount = amount / self.rates[from_code]
        
        # Convert to target currency
        return base_amount * self.rates[to_code]

# Usage
converter = CurrencyConverter()
eur_amount = converter.convert(Decimal('100'), 'USD', 'EUR')
print(f"100 USD = {eur_amount} EUR")
```

## Troubleshooting

### Rates Not Syncing

1. Check BCC API availability
2. Verify `OXI_BCC_FALLBACK_ON_OXR` setting
3. Check network connectivity
4. Review logs for specific errors

### Missing Currencies

Ensure the currency code is in `AVAILABLES_CURRENCIES` list.

### Stale Rates

Check when the last sync occurred:
```python
state = CurrencyState.objects.latest()
print(f"Last sync: {state.created_at}")
```

## Dependencies

- `bcc-rates`: Library for fetching rates from BCC and OpenExchangeRates
- `structlog`: Structured logging
- `django-ninja-extra`: REST API framework
