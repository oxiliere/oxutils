from ninja_extra.permissions import BasePermission
from oxutils.oxiliere.models import TenantUser
from oxutils.constants import OXILIERE_SERVICE_TOKEN
from oxutils.jwt.tokens import OxilierServiceToken


class TenantPermission(BasePermission):
    """
    Vérifie que l'utilisateur a accès au tenant actuel.
    L'utilisateur doit être authentifié et avoir un lien avec le tenant.
    """
    def has_permission(self, request, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request, 'tenant'):
            return False
        
        # Vérifier que l'utilisateur a accès à ce tenant
        return TenantUser.objects.filter(
            tenant__pk=request.tenant.pk,
            user__pk=request.user.pk
        ).exists()


class TenantOwnerPermission(BasePermission):
    """
    Vérifie que l'utilisateur est propriétaire (owner) du tenant actuel.
    """
    def has_permission(self, request, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request, 'tenant'):
            return False
        
        return TenantUser.objects.filter(
            tenant__pk=request.tenant.pk,
            user__pk=request.user.pk,
            is_owner=True
        ).exists()


class TenantAdminPermission(BasePermission):
    """
    Vérifie que l'utilisateur est admin ou owner du tenant actuel.
    """
    def has_permission(self, request, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request, 'tenant'):
            return False
        
        return TenantUser.objects.filter(
            tenant__pk=request.tenant.pk,
            user__pk=request.user.pk,
            is_admin=True
        ).exists()


class TenantUserPermission(BasePermission):
    """
    Vérifie que l'utilisateur est un membre du tenant actuel.
    Alias de TenantPermission pour plus de clarté sémantique.
    """
    def has_permission(self, request, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request, 'tenant'):
            return False
        
        return TenantUser.objects.filter(
            tenant__pk=request.tenant.pk,
            user__pk=request.user.pk
        ).exists()


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
