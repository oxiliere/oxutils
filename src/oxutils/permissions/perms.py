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
