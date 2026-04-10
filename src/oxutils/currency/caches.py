from cacheops import cached_as
from oxutils.currency.models import CurrencyState



@cached_as(CurrencyState)
def get_latest_currency_rates():
    return CurrencyState.objects.latest()
