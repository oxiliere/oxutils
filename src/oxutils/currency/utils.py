import time
from django.conf import settings
from django.db import transaction
from bcc_rates import BCCBankSource, OXRBankSource, SourceValue
from oxutils.currency.enums import CurrencySource
from oxutils.currency.schemas import CurrencyStateDetailSchema
import structlog

logger = structlog.get_logger(__name__)


def load_rates() -> tuple[list[SourceValue], CurrencySource]:
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            bcc_source = BCCBankSource()
            rates = bcc_source.sync(cache=True)
            return rates, CurrencySource.BCC
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(1)
            else:
                if not getattr(settings, 'OXI_BCC_FALLBACK_ON_OXR', False):
                    raise Exception(f"Failed to load rates from BCC: {str(e)}")
                break
    
    try:
        oxr_source = OXRBankSource()
        rates = oxr_source.sync(cache=True)
        return rates, CurrencySource.OXR
    except Exception as e:
        raise Exception(f"Failed to load rates from both BCC and OXR: {str(e)}")

@transaction.atomic
def update_rates(state: CurrencyStateDetailSchema):
    from oxutils.currency.models import CurrencyState, Currency 

    if CurrencyState.objects.filter(id=state.id).exists():
        logger.info("currency_state_exists", id=state.id)
        return

    if not len(state.currencies.keys()):
        logger.info("currency_state_no_currencies", id=state.id)
        return

    _state = CurrencyState.objects.create(
        id=state.id,
        source=state.source,
        created_at=state.created_at,
        updated_at=state.updated_at,
    )

    currencies = []

    for key, value in state.currencies.items():
        currencies.append(
            Currency(
                code=key,
                rate=value,
                state=_state
            )
        )

    Currency.objects.bulk_create(currencies)

    logger.info("currency_state_updated", id=state.id)
