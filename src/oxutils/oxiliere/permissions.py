import structlog

from ninja_extra.permissions import BasePermission
from oxutils.constants import OXILIERE_SERVICE_TOKEN
from oxutils.jwt.tokens import OxilierServiceToken
from oxutils.jwt.models import TokenTenant



logger = structlog.get_logger(__name__)




class TenantBasePermission(BasePermission):
    """
    Vérifie que l'utilisateur a accès au tenant actuel.
    L'utilisateur doit être authentifié et avoir un lien avec le tenant.
    """
    def check_tenant_permission(self, request) -> bool:
        raise NotImplementedError("Subclasses must implement this method")

    def has_permission(self, request, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request, 'tenant'):
            logger.warning('tenant_permission', type="tenant_not_found")
            return False

        if not isinstance(request.tenant, TokenTenant):
            logger.warning(
                'tenant_permission', 
                type="tenant_is_not_token_tenant", 
                tenant=request.tenant,
            )
            return False

        return self.check_tenant_permission(request)


class TenantUserPermission(TenantBasePermission):
    """
    Vérifie que l'utilisateur est un membre du tenant actuel.
    Alias de TenantPermission pour plus de clarté sémantique.
    """
    def check_tenant_permission(self, request) -> bool:
        tenant: TokenTenant = request.tenant

        logger.info(
            'tenant_permission', 
            type="tenant_user_access_permission", 
            tenant=tenant, passed=tenant.is_tenant_user
        )
        
        return tenant.is_tenant_user


class TenantOwnerPermission(TenantBasePermission):
    """
    Vérifie que l'utilisateur est propriétaire (owner) du tenant actuel.
    """
    def check_tenant_permission(self, request) -> bool:
        tenant: TokenTenant = request.tenant

        logger.info(
            'tenant_permission', 
            type="tenant_user_access_permission", 
            tenant=tenant, passed=tenant.is_owner_user
        )
        
        return tenant.is_owner_user


class TenantAdminPermission(TenantBasePermission):
    """
    Vérifie que l'utilisateur est admin ou owner du tenant actuel.
    """
    def check_tenant_permission(self, request) -> bool:
        tenant: TokenTenant = request.tenant

        logger.info(
            'tenant_permission', 
            type="tenant_user_access_permission", 
            tenant=tenant, passed=tenant.is_admin_user
        )
        
        return tenant.is_admin_user


class OxiliereServicePermission(BasePermission):
    """
    Vérifie que la requête provient d'un service interne Oxiliere.
    Utilise un token de service ou une clé API spéciale.
    """
    def has_permission(self, request, **kwargs):
        custom = 'HTTP_' + OXILIERE_SERVICE_TOKEN.upper().replace('-', '_')
        service_token = request.headers.get(OXILIERE_SERVICE_TOKEN) or request.META.get(custom)
        
        if not service_token:
            return False
        
        try:
            OxilierServiceToken(token=service_token)
            return True
        except Exception:
            return False



IsTenantUser = TenantUserPermission()
IsTenantOwner = TenantOwnerPermission()
IsTenantAdmin = TenantAdminPermission()
IsOxiliereService = OxiliereServicePermission()
