import time
from django.conf import settings
from bcc_rates import BCCBankSource, OXRBankSource, SourceValue
from oxutils.currency.enums import CurrencySource



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
