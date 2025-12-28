from django.contrib.sites.shortcuts import RequestSite
from django.dispatch import receiver
import structlog
from django_structlog import signals
from oxutils.settings import oxi_settings
from oxutils.oxiliere.context import get_current_tenant_schema_name


@receiver(signals.bind_extra_request_metadata)
def bind_domain(request, logger, **kwargs):
    current_site = RequestSite(request)
    ctx = {
        'domain': current_site.domain,
        'user_id': str(request.user.pk),
        'service': oxi_settings.service_name
    }
    if oxi_settings.multitenancy:
        ctx['tenant'] = get_current_tenant_schema_name()

    structlog.contextvars.bind_contextvars(**ctx)
