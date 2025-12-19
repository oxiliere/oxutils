from django.contrib.sites.shortcuts import RequestSite
from django.dispatch import receiver
import structlog
from django_structlog import signals
from oxutils.settings import oxi_settings



@receiver(signals.bind_extra_request_metadata)
def bind_domain(request, logger, **kwargs):
    current_site = RequestSite(request)
    structlog.contextvars.bind_contextvars(
        domain=current_site.domain,
        user_id=str(request.user.pk),
        service=oxi_settings.service_name
    )
