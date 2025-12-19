from typing import Optional
from django.db import models
from django.db import transaction
import structlog
from oxutils.models import (
    UUIDPrimaryKeyMixin,
    TimestampMixin,
)
from .enums import CurrencySource
from .utils import load_rates



logger = structlog.get_logger(__name__)


AVAILABLES_CURRENCIES = [
    "AOA",   
    "AUD",   
    "BIF",   
    "CAD",   
    "CHF",   
    "CNY",   
    "EUR",
    "GBP",
    "JPY",    
    "RWF",    
    "TZS",    
    "UGX",    
    "USD",    
    "XAF",    
    "XDR",    
    "ZAR",
    "ZMW"
]


class CurrencyStateManager(models.Manager):
    def latest(self):
        return self.get_queryset().prefetch_related("currencies").latest("created_at")

class CurrencyState(UUIDPrimaryKeyMixin, TimestampMixin):
    source = models.CharField(max_length=10, choices=CurrencySource.choices)
    objects = CurrencyStateManager()
    
    @classmethod
    def sync(cls) -> Optional['CurrencyState']:
        rates, source = load_rates()
        currencies = []

        if not rates:
            logger.error("currency_state_sync_failed", source=source)
            raise ValueError("No rates found")

        with transaction.atomic():
            state = cls.objects.create(source=source)

            for rate in rates:
                currency = Currency(
                    code=rate.currency,
                    rate=rate.amount,
                    state=state
                )
                currencies.append(currency)

            Currency.objects.bulk_create(currencies)

            logger.info("currency_state_synced", state=state.id, source=source)

            return state


class Currency(UUIDPrimaryKeyMixin):
    code = models.CharField(max_length=10)
    rate = models.DecimalField(max_digits=10, decimal_places=4)
    state = models.ForeignKey(
        CurrencyState, 
        on_delete=models.CASCADE,
        related_name="currencies"
    )

    class Meta:
        ordering = ['code']
        indexes = [
            models.Index(fields=['code', 'state']),
        ]

    def __str__(self):
        return f"{self.code} - {self.rate}"

    def clean(self):
        if self.code not in AVAILABLES_CURRENCIES:
            raise ValueError(f"Invalid currency code: {self.code}")

        if self.rate <= 0:
            raise ValueError(f"Invalid currency rate: {self.rate}")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
