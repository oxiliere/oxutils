import structlog
from ninja_extra.permissions import BasePermission

logger = structlog.get_logger(__name__)


class TenantBasePermission(BasePermission):
    """
    Vérifie que l'utilisateur a accès au tenant actuel.
    L'utilisateur doit être authentifié et avoir un lien avec le tenant.
    """

    def check_tenant_permission(self, request) -> bool:
        raise NotImplementedError("Subclasses must implement this method")

    def has_permission(self, request, controller=None, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request, "tenant") or not request.tenant:
            logger.warning("tenant_permission", type="tenant_not_found")
            return False

        if not hasattr(request.tenant, "user") or not request.tenant.user:
            logger.warning(
                "tenant_permission",
                type="tenant_user_not_attached",
                tenant=getattr(request.tenant, "oxi_id", None),
            )
            return False

        return self.check_tenant_permission(request)


class TenantUserPermission(TenantBasePermission):
    """
    Vérifie que l'utilisateur est un membre du tenant actuel.
    Alias de TenantPermission pour plus de clarté sémantique.
    """

    def check_tenant_permission(self, request) -> bool:
        tenant = request.tenant
        passed = getattr(tenant.user, "status", None) == "active"

        logger.info(
            "tenant_permission",
            type="tenant_user_access_permission",
            tenant=tenant.oxi_id,
            passed=passed,
        )

        return passed


class TenantOwnerPermission(TenantBasePermission):
    """
    Vérifie que l'utilisateur est propriétaire (owner) du tenant actuel.
    """

    def check_tenant_permission(self, request) -> bool:
        tenant = request.tenant
        active = getattr(tenant.user, "status", None) == "active"
        passed = active and getattr(tenant.user, "is_owner", False)

        logger.info(
            "tenant_permission",
            type="tenant_user_access_permission",
            tenant=tenant.oxi_id,
            passed=passed,
        )

        return passed


class TenantAdminPermission(TenantBasePermission):
    """
    Vérifie que l'utilisateur est admin ou owner du tenant actuel.
    """

    def check_tenant_permission(self, request) -> bool:
        tenant = request.tenant
        active = getattr(tenant.user, "status", None) == "active"
        passed = active and getattr(tenant.user, "is_admin", False)

        logger.info(
            "tenant_permission",
            type="tenant_user_access_permission",
            tenant=tenant.oxi_id,
            passed=passed,
        )

        return passed


IsTenantUser = TenantUserPermission()
IsTenantOwner = TenantOwnerPermission()
IsTenantAdmin = TenantAdminPermission()
