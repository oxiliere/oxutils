from django.conf import settings
from django.db import connection
from django.http import Http404
from django.urls import set_urlconf
from django.utils.module_loading import import_string
from django.utils.deprecation import MiddlewareMixin

from django_tenants.utils import (
    get_public_schema_name,
    get_public_schema_urlconf,
    get_tenant_types,
    has_multi_type_tenants,
)
from oxutils.settings import oxi_settings
from oxutils.constants import (
    ORGANIZATION_HEADER_KEY,
    ORGANIZATION_TOKEN_COOKIE_KEY
)
from oxutils.oxiliere.utils import is_system_tenant
from oxutils.jwt.models import TokenTenant
from oxutils.jwt.tokens import OrganizationAccessToken
from oxutils.oxiliere.context import set_current_tenant_schema_name




class TenantMainMiddleware(MiddlewareMixin):
    TENANT_NOT_FOUND_EXCEPTION = Http404
    """
    This middleware should be placed at the very top of the middleware stack.
    Selects the proper database schema using the request host. Can fail in
    various ways which is better than corrupting or revealing data.
    """

    @staticmethod
    def get_org_id_from_request(request):
        """ Extracts organization ID from request header X-Organization-ID.
        """
        custom = 'HTTP_' + ORGANIZATION_HEADER_KEY.upper().replace('-', '_')
        return request.headers.get(ORGANIZATION_HEADER_KEY) or request.META.get(custom)

    def get_tenant(self, tenant_model, oxi_id):
        """ Get tenant by oxi_id instead of domain.
        """
        return tenant_model.objects.get(oxi_id=oxi_id)

    def process_request(self, request):
        # Connection needs first to be at the public schema, as this is where
        # the tenant metadata is stored.

        connection.set_schema_to_public()
        
        oxi_id = self.get_org_id_from_request(request)

        # Try to get tenant from cookie token first
        tenant_token = request.COOKIES.get(ORGANIZATION_TOKEN_COOKIE_KEY)
        tenant = None
        request._should_set_tenant_cookie = False
        
        if tenant_token:
            tenant = TokenTenant.for_token(tenant_token)
            # Verify the token's oxi_id matches the request
            if not is_system_tenant(tenant) and tenant.oxi_id != oxi_id:
                tenant = None
        
        # If no valid token, fetch from database
        if not tenant:
            if oxi_id: # fetch with oxi_id on tenant
                tenant_model = connection.tenant_model
                try:
                    tenant = self.get_tenant(tenant_model, oxi_id)
                    # Mark that we need to set the cookie in the response
                    request._should_set_tenant_cookie = True
                except tenant_model.DoesNotExist:
                    default_tenant = self.no_tenant_found(request, oxi_id)
                    return default_tenant
            else: # try to return the system tenant
                try:
                    from oxutils.oxiliere.caches import get_system_tenant
                    tenant = get_system_tenant()
                    request._should_set_tenant_cookie = True
                except Exception as e:
                    from django.http import HttpResponseBadRequest
                    return HttpResponseBadRequest('Missing X-Organization-ID header')

        request.tenant = tenant
        set_current_tenant_schema_name(tenant.schema_name)
        connection.set_tenant(request.tenant)
        self.setup_url_routing(request)

    def process_response(self, request, response):
        """Set the tenant token cookie if needed."""
        if hasattr(request, '_should_set_tenant_cookie') and request._should_set_tenant_cookie:
            if hasattr(request, 'tenant') and not isinstance(request.tenant, TokenTenant):
                # Generate token from DB tenant
                token = OrganizationAccessToken.for_tenant(request.tenant)
                response.set_cookie(
                    key=ORGANIZATION_TOKEN_COOKIE_KEY,
                    value=str(token),
                    max_age=60 * oxi_settings.jwt_org_access_token_lifetime,
                    httponly=True,
                    secure=getattr(settings, 'SESSION_COOKIE_SECURE', False),
                    samesite='Lax',
                )
        return response

    def no_tenant_found(self, request, oxi_id):
        """ What should happen if no tenant is found.
        This makes it easier if you want to override the default behavior """
        if hasattr(settings, 'DEFAULT_NOT_FOUND_TENANT_VIEW'):
            view_path = settings.DEFAULT_NOT_FOUND_TENANT_VIEW
            view = import_string(view_path)
            if hasattr(view, 'as_view'):
                response = view.as_view()(request)
            else:
                response = view(request)
            if hasattr(response, 'render'):
                response.render()
            return response
        elif hasattr(settings, 'SHOW_PUBLIC_IF_NO_TENANT_FOUND') and settings.SHOW_PUBLIC_IF_NO_TENANT_FOUND:
            self.setup_url_routing(request=request, force_public=True)
        else:
            raise self.TENANT_NOT_FOUND_EXCEPTION('No tenant for X-Organization-ID "%s"' % oxi_id)

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
            if (not hasattr(request, 'tenant') or
                    ((force_public or request.tenant.schema_name == get_public_schema_name()) and
                     'URLCONF' in tenant_types[public_schema_name])):
                request.urlconf = get_public_schema_urlconf()
            else:
                tenant_type = request.tenant.get_tenant_type()
                request.urlconf = tenant_types[tenant_type]['URLCONF']
            set_urlconf(request.urlconf)

        else:
            # Do we have a public-specific urlconf?
            if (hasattr(settings, 'PUBLIC_SCHEMA_URLCONF') and
                    (force_public or request.tenant.schema_name == get_public_schema_name())):
                request.urlconf = settings.PUBLIC_SCHEMA_URLCONF
