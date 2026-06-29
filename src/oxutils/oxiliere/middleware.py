import structlog
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.http import Http404, HttpResponse
from django.urls import set_urlconf
from django.utils.deprecation import MiddlewareMixin
from django.utils.module_loading import import_string
from django_tenants.utils import (
    get_public_schema_name,
    get_public_schema_urlconf,
    get_tenant_model,
    get_tenant_types,
    has_multi_type_tenants,
)

from oxutils.constants import ORGANIZATION_HEADER_KEY
from oxutils.oxiliere.cacheops import (
    delete_cached_tenant_token,
    get_cached_tenant_token,
)
from oxutils.oxiliere.context import set_current_tenant_schema_name
from oxutils.oxiliere.enums import TenantStatus

logger = structlog.get_logger(__name__)


class TenantMainMiddleware(MiddlewareMixin):
    TENANT_NOT_FOUND_EXCEPTION = Http404
    """
    This middleware should be placed at the very top of the middleware stack.
    Selects the proper database schema using the request host. Can fail in
    various ways which is better than corrupting or revealing data.
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.tenant_model = get_tenant_model()

    @staticmethod
    def get_org_id_from_request(request):
        """Extracts organization ID from request header X-Organization-ID."""
        custom = "HTTP_" + ORGANIZATION_HEADER_KEY.upper().replace("-", "_")
        return request.headers.get(ORGANIZATION_HEADER_KEY) or request.META.get(custom)

    def get_tenant(self, oxi_id):
        """Get tenant by oxi_id instead of domain."""
        return self.tenant_model.objects.get(oxi_id=oxi_id)

    def get_tenant_user(self, tenant, user, raise_exception=False):
        """Get tenant user by tenant and user."""
        if not tenant or not user:
            if raise_exception:
                raise ObjectDoesNotExist("tenant_user_not_found, tenant or user is None")
            return None

        try:
            return tenant.users.select_related("user").get(user__pk=user.id, status="active")
        except ObjectDoesNotExist as exc:
            logger.error("tenant_user_not_found", tenant_id=tenant.id, user_id=user.id, exc_info=exc)
            if raise_exception:
                raise ObjectDoesNotExist("tenant_user_not_found") from exc
            return None

    def process_request(self, request):
        # Connection needs first to be at the public schema, as this is where
        # the tenant metadata is stored.

        connection.set_schema_to_public()

        oxi_id = self.get_org_id_from_request(request)
        tenant = None

        # ── Normal path: org + user → cache (or DB on miss) ──────────
        if oxi_id and hasattr(request, "user") and request.user and request.user.is_authenticated:
            user_id = str(request.user.id)
            try:
                tenant = get_cached_tenant_token(oxi_id, user_id)
            except ObjectDoesNotExist:
                logger.info("tenant_not_found", oxi_id=oxi_id, user_id=user_id)
                return self.no_tenant_found(request, oxi_id)

        elif not oxi_id:
            # ── No org header → system tenant ────────────────────────
            try:
                from oxutils.oxiliere.caches import get_system_tenant

                tenant = get_system_tenant()

                if hasattr(request, "user") and request.user:
                    tenant.user = self.get_tenant_user(
                        tenant, request.user, raise_exception=False
                    )
                else:
                    tenant.user = None
            except Exception as e:
                logger.error("system_tenant_not_found", error=str(e))
                from django.http import HttpResponseBadRequest

                return HttpResponseBadRequest("Missing X-Organization-ID header")
        else:
            # oxi_id present but no authenticated user
            return self.no_tenant_found(request, oxi_id)

        # ── Status guards ─────────────────────────────────────────────
        if tenant.is_deleted or not tenant.is_active:
            logger.error("tenant_is_deleted_or_inactive", oxi_id=oxi_id)
            if oxi_id and hasattr(request, "user") and request.user and request.user.is_authenticated:
                delete_cached_tenant_token(oxi_id, str(request.user.id))
            return self.no_tenant_found(request, oxi_id)

        status_response = self._handle_tenant_status(request, tenant)
        if status_response is not None:
            return status_response

        # ── Attach tenant to request ──────────────────────────────────
        request.db_tenant = None
        request.tenant = tenant

        set_current_tenant_schema_name(tenant.schema_name)
        connection.set_tenant(request.tenant)
        self.setup_url_routing(request)

    def process_response(self, request, response):
        """Cache is handled by :func:`get_cached_tenant_token` — nothing to do."""
        return response

    def no_tenant_found(self, request, oxi_id):
        """What should happen if no tenant is found.
        This makes it easier if you want to override the default behavior"""
        if hasattr(settings, "DEFAULT_NOT_FOUND_TENANT_VIEW"):
            view_path = settings.DEFAULT_NOT_FOUND_TENANT_VIEW
            view = import_string(view_path)
            if hasattr(view, "as_view"):
                response = view.as_view()(request)
            else:
                response = view(request)
            if hasattr(response, "render"):
                response.render()
            return response
        elif (
            hasattr(settings, "SHOW_PUBLIC_IF_NO_TENANT_FOUND")
            and settings.SHOW_PUBLIC_IF_NO_TENANT_FOUND
        ):
            self.setup_url_routing(request=request, force_public=True)
        else:
            raise self.TENANT_NOT_FOUND_EXCEPTION('No tenant for X-Organization-ID "%s"' % oxi_id)

    # ── Status handling ─────────────────────────────────────────────

    def _handle_tenant_status(self, request, tenant):
        """Return an HttpResponse for non-ACTIVE tenants, or None to proceed."""
        oxi_id = self.get_org_id_from_request(request)
        status = getattr(tenant, "status", None)

        handlers = {
            TenantStatus.PENDING_MIGRATION: self._pending_migration_response,
            TenantStatus.SUSPENDED: self._suspended_response,
            TenantStatus.INACTIVE: self._inactive_response,
        }

        handler = handlers.get(status)
        if handler:
            logger.info(f"tenant_{status}", oxi_id=oxi_id)
            return handler(oxi_id)
        return None

    @staticmethod
    def _pending_migration_response(oxi_id):
        response = HttpResponse(
            content=b'{"detail":"Tenant setup is in progress. Please try again shortly.","code":"pending_setup"}',
            content_type="application/json",
            status=503,
        )
        response["Retry-After"] = "30"
        return response

    @staticmethod
    def _suspended_response(oxi_id):
        return HttpResponse(
            content=b'{"detail":"This tenant has been suspended.","code":"locked"}',
            content_type="application/json",
            status=423,
        )

    @staticmethod
    def _inactive_response(oxi_id):
        return HttpResponse(
            content=b'{"detail":"This tenant is currently inactive.","code":"inactive"}',
            content_type="application/json",
            status=404,
        )

    @staticmethod
    def setup_url_routing(request, force_public=False):
        """
        Sets the correct url conf based on the tenant
        :param request:
        :param force_public
        """
        public_schema_name = get_public_schema_name()
        if has_multi_type_tenants():
            tenant_types = get_tenant_types()
            if not hasattr(request, "tenant") or (
                (force_public or request.tenant.schema_name == get_public_schema_name())
                and "URLCONF" in tenant_types[public_schema_name]
            ):
                request.urlconf = get_public_schema_urlconf()
            else:
                tenant_type = request.tenant.get_tenant_type()
                request.urlconf = tenant_types[tenant_type]["URLCONF"]
            set_urlconf(request.urlconf)

        else:
            # Do we have a public-specific urlconf?
            if hasattr(settings, "PUBLIC_SCHEMA_URLCONF") and (
                force_public or request.tenant.schema_name == get_public_schema_name()
            ):
                request.urlconf = settings.PUBLIC_SCHEMA_URLCONF
