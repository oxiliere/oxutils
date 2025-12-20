from django.http import HttpRequest
from django.core.exceptions import ObjectDoesNotExist
from ninja_extra import (
    ControllerBase,
    api_controller,
    http_get,
)
from ninja_extra.pagination import (
    paginate, PageNumberPaginationExtra, PaginatedResponseSchema
)
from ninja.errors import HttpError
from uuid import UUID
import structlog
from oxutils.currency.models import CurrencyState
from oxutils.currency.schemas import (
    CurrencyStateSchema,
    CurrencyStateDetailSchema,
)


logger = structlog.get_logger(__name__)


@api_controller('/currency', tags=['Currency'], auth=None)
class CurrencyController(ControllerBase):
    
    @http_get('/states', response=PaginatedResponseSchema[CurrencyStateSchema])
    @paginate(PageNumberPaginationExtra, page_size=20)
    def list_states(self, request: HttpRequest):
        return CurrencyState.objects.all().order_by('-created_at')
    
    @http_get('/states/latest', response=CurrencyStateDetailSchema)
    def get_latest_state(self, request: HttpRequest):
        try:
            state = CurrencyState.objects.latest()
        except ObjectDoesNotExist:
            logger.error("currency_state_not_found", message="No currency state found in database")
            raise HttpError(404, "No currency state found in database")
        
        return {
            'id': state.id,
            'source': state.source,
            'created_at': state.created_at,
            'updated_at': state.updated_at,
            'currencies': {c.code: float(c.rate) for c in state.currencies.all()}
        }
    
    @http_get('/states/{state_id}', response=CurrencyStateDetailSchema)
    def get_state(self, request: HttpRequest, state_id: UUID):
        state = CurrencyState.objects.prefetch_related('currencies').get(id=state_id)
        return {
            'id': state.id,
            'source': state.source,
            'created_at': state.created_at,
            'updated_at': state.updated_at,
            'currencies': {c.code: float(c.rate) for c in state.currencies.all()}
        }
    
    @http_get('/rates', response=dict[str, float])
    def get_current_rates(self, request: HttpRequest):
        try:
            state = CurrencyState.objects.latest()
        except ObjectDoesNotExist:
            logger.error("currency_state_not_found", message="No currency state found in database")
            raise HttpError(404, "No currency rates available")
        
        currencies = state.currencies.all()
        return {c.code: float(c.rate) for c in currencies}
    
    @http_get('/rates/{code}', response=dict[str, float])
    def get_rate_by_code(self, request: HttpRequest, code: str):
        try:
            state = CurrencyState.objects.latest()
            currency = state.currencies.get(code=code.upper())
        except ObjectDoesNotExist:
            logger.error("currency_rate_not_found", code=code.upper())
            raise HttpError(404, f"Currency rate for {code.upper()} not found")
        
        return {currency.code: float(currency.rate)}
