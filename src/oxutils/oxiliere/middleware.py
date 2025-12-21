from django.conf import settings
from django.db import connection
from django.http import Http404
from django.urls import set_urlconf
from django.utils.module_loading import import_string
from django.utils.deprecation import MiddlewareMixin

from django_tenants.utils import (
    get_public_schema_name,
    get_public_schema_urlconf
)
from oxutils.constants import ORGANIZATION_HEADER_KEY

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
        if not oxi_id:
            from django.http import HttpResponseBadRequest
            return HttpResponseBadRequest('Missing X-Organization-ID header')

        tenant_model = connection.tenant_model
        try:
            tenant = self.get_tenant(tenant_model, oxi_id)
        except tenant_model.DoesNotExist:
            default_tenant = self.no_tenant_found(request, oxi_id)
            return default_tenant

        request.tenant = tenant
        connection.set_tenant(request.tenant)
        self.setup_url_routing(request)

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
