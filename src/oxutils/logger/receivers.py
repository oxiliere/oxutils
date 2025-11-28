from django.contrib.sites.shortcuts import RequestSite
from django.dispatch import receiver
from django_structlog import signals
from cid.locals import get_cid
import structlog



@receiver(signals.bind_extra_request_metadata)
def bind_domain(request, logger, **kwargs):
    current_site = RequestSite(request)
    structlog.contextvars.bind_contextvars(
        domain=current_site.domain,
        cid=get_cid()
    )


@receiver(signals.bind_extra_request_metadata)
def bind_token_user_id(request, logger, **kwargs):
    structlog.contextvars.bind_contextvars(user_id=str(request.user.pk))
