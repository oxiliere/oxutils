from typing import Optional
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from ninja_extra.permissions import BasePermission
from ninja_extra.controllers import ControllerBase

from oxutils.permissions.utils import str_check



class ScopePermission(BasePermission):
    """
    Permission class for checking user permissions using the string format.
    
    Format: "<scope>:<actions>:<group>?key=value"
    
    Example:
        @api_controller('/articles', permissions=[ScopePermission('articles:w:staff')])
        class ArticleController:
            pass
    """

    def __init__(self, perm: str, ctx: Optional[dict] = None):
        """
        Initialize the permission checker.
        
        Args:
            perm: Permission string in format "<scope>:<actions>:<group>?context"
        """
        self.perm = perm
        self.ctx = ctx if ctx else dict()

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        """
        Check if the user has the required permission.
        
        Args:
            request: HTTP request object
            controller: Controller instance
            
        Returns:
            True if user has permission, False otherwise
        """
        return str_check(request.user, self.perm, **self.ctx)


class ScopeAnyPermission(BasePermission):
    """
    Permission class for checking if user has at least one of multiple permissions.
    
    Vérifie si l'utilisateur possède au moins une des permissions fournies.
    Utilise any_permission_check pour une vérification optimisée en une seule requête.
    
    Example:
        @api_controller('/articles', permissions=[
            ScopeAnyPermission('articles:r', 'articles:w:staff', 'articles:d:admin')
        ])
        class ArticleController:
            # User needs either read access, OR staff write access, OR admin delete access
            pass
    """

    def __init__(self, *perms: str):
        """
        Initialize the permission checker with multiple permission strings.
        
        Args:
            *perms: Variable number of permission strings in format "<scope>:<actions>:<group>?context"
        """
        if not perms:
            raise ValueError("At least one permission string must be provided")
        self.perms = perms

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        """
        Check if the user has at least one of the required permissions.
        
        Args:
            request: HTTP request object
            controller: Controller instance
            
        Returns:
            True if user has at least one permission, False otherwise
        """
        from oxutils.permissions.caches import cache_any_permission_check
        return cache_any_permission_check(request.user, *self.perms)


class ScopeAnyActionPermission(BasePermission):
    """
    Permission class for checking if user has at least one of multiple actions on a scope.
    
    Vérifie si l'utilisateur possède au moins une des actions requises pour un scope donné.
    La chaîne d'actions contient plusieurs actions dont au moins une est requise.
    
    Example:
        @api_controller('/articles', permissions=[
            ScopeAnyActionPermission('articles:rwd:staff')
        ])
        class ArticleController:
            # User needs read OR write OR delete access on articles in staff group
            pass
            
        @api_controller('/invoices', permissions=[
            ScopeAnyActionPermission('invoices:rw?tenant_id=123')
        ])
        class InvoiceController:
            # User needs read OR write access on invoices with tenant_id=123
            pass
    """

    def __init__(self, perm: str, ctx: Optional[dict] = None):
        """
        Initialize the permission checker with a permission string.
        
        Args:
            perm: Permission string in format "<scope>:<actions>:<group>?context"
                  where actions contains multiple characters (e.g., 'rwd' for read OR write OR delete)
            ctx: Optional additional context dict
        """
        if not perm:
            raise ValueError("Permission string must be provided")
        
        self.perm = perm
        self.ctx = ctx if ctx else dict()

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        """
        Check if the user has at least one of the required actions.
        
        Args:
            request: HTTP request object
            controller: Controller instance
            
        Returns:
            True if user has at least one action, False otherwise
        """
        from oxutils.permissions.caches import cache_any_action_check
        from oxutils.permissions.utils import parse_permission
        
        scope, actions, group, query_context = parse_permission(self.perm)
        final_context = {**query_context, **self.ctx}
        
        return cache_any_action_check(
            request.user,
            scope,
            actions,
            group,
            **final_context
        )


def access_manager(actions: str):
    """
    Factory function for creating ScopePermission instances for access manager.
    
    Builds a permission string from settings:
    - ACCESS_MANAGER_SCOPE: The scope to check
    - ACCESS_MANAGER_GROUP: Optional group filter
    - ACCESS_MANAGER_CONTEXT: Optional context dict converted to query params
    
    Args:
        actions: Actions required (e.g., 'r', 'rw', 'rwd')
        
    Returns:
        ScopePermission instance configured with access manager settings
        
    Raises:
        ImproperlyConfigured: If required settings are missing
        
    Example:
        @api_controller('/access', permissions=[access_manager('w')])
        class AccessController:
            pass
    """
    # Validate required settings
    if not hasattr(settings, 'ACCESS_MANAGER_SCOPE'):
        raise ImproperlyConfigured(
            'ACCESS_MANAGER_SCOPE is not defined. '
            'Add ACCESS_MANAGER_SCOPE = "access" to your settings.'
        )
    
    # Build base permission string: scope:actions
    perm = f"{settings.ACCESS_MANAGER_SCOPE}:{actions}"
    
    # Add group if defined and not None
    if hasattr(settings, 'ACCESS_MANAGER_GROUP') and settings.ACCESS_MANAGER_GROUP is not None:
        perm += f":{settings.ACCESS_MANAGER_GROUP}"
    
    # Get context if defined and not empty
    context = {}
    if hasattr(settings, 'ACCESS_MANAGER_CONTEXT') and settings.ACCESS_MANAGER_CONTEXT:
        context = settings.ACCESS_MANAGER_CONTEXT
        if not isinstance(context, dict):
            raise ImproperlyConfigured(
                'ACCESS_MANAGER_CONTEXT must be a dictionary. '
                f'Got {type(context).__name__} instead.'
            )
    
    return ScopePermission(perm, context)
