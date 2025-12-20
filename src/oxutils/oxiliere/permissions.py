from ninja.permissions import BasePermission
from django.conf import settings
from oxutils.oxiliere.models import TenantUser


class TenantPermission(BasePermission):
    """
    Vérifie que l'utilisateur a accès au tenant actuel.
    L'utilisateur doit être authentifié et avoir un lien avec le tenant.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request, 'tenant'):
            return False
        
        # Vérifier que l'utilisateur a accès à ce tenant
        return TenantUser.objects.filter(
            tenant=request.tenant,
            user=request.user
        ).exists()


class TenantOwnerPermission(BasePermission):
    """
    Vérifie que l'utilisateur est propriétaire (owner) du tenant actuel.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request, 'tenant'):
            return False
        
        # Vérifier que l'utilisateur est owner du tenant
        return TenantUser.objects.filter(
            tenant=request.tenant,
            user=request.user,
            is_owner=True
        ).exists()


class TenantAdminPermission(BasePermission):
    """
    Vérifie que l'utilisateur est admin ou owner du tenant actuel.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request, 'tenant'):
            return False
        
        # Vérifier que l'utilisateur est admin ou owner du tenant
        return TenantUser.objects.filter(
            tenant=request.tenant,
            user=request.user,
            is_admin=True
        ).exists() or TenantUser.objects.filter(
            tenant=request.tenant,
            user=request.user,
            is_owner=True
        ).exists()


class TenantUserPermission(BasePermission):
    """
    Vérifie que l'utilisateur est un membre du tenant actuel.
    Alias de TenantPermission pour plus de clarté sémantique.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request, 'tenant'):
            return False
        
        return TenantUser.objects.filter(
            tenant=request.tenant,
            user=request.user
        ).exists()


class OxiliereServicePermission(BasePermission):
    """
    Vérifie que la requête provient d'un service interne Oxiliere.
    Utilise un token de service ou une clé API spéciale.
    """
    def has_permission(self, request, view):
        # Vérifier le header de service
        service_token = request.headers.get('X-Oxiliere-Service-Token')
        
        if not service_token:
            return False
        
        # Comparer avec le token configuré dans settings
        expected_token = getattr(settings, 'OXILIERE_SERVICE_TOKEN', None)
        
        if not expected_token:
            return False
        
        return service_token == expected_token

