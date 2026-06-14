"""
Signals for the currency module.
"""
from django.dispatch import Signal

currency_sync_succeeded = Signal()
"""
Fired when a currency sync completes successfully.

Args:
    sender: The CurrencyState class.
    state: The newly created CurrencyState instance.
    source: The CurrencySource used (BCC or OXR).
    count: Number of currencies loaded.
"""

currency_sync_failed = Signal()
"""
Fired when a currency sync fails.

Args:
    sender: The CurrencyState class.
    error: The exception that caused the failure.
    source: The CurrencySource attempted (None if unknown).
"""
