from functools import lru_cache
from typing import Optional

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.utils.module_loading import import_string
from ninja_extra.controllers import ControllerBase
from ninja_extra.permissions import BasePermission

from oxutils.permissions.utils import str_check


class ScopePermission(BasePermission):
    """
    Permission class for checking user permissions using named actions.

    Format:
        ``<scope>:<action>``                      — single action
        ``<scope>:<action1>/<action2>``           — AND (all actions required)
        ``<scope>:<action1>|<action2>``           — OR (at least one action)
        ``<scope>:<action1>/<action2>:<role>``    — AND with role filter
        ``<scope>:<action1>|<action2>:<role>``    — OR with role filter
        ``<scope>:<action1>/<action2>?key=value``  — with context

    Example:
        @api_controller('/orders', permissions=[ScopePermission('orders:create/approve')])
        class OrderController:
            # User needs create AND approve on orders
            pass

        @api_controller('/orders', permissions=[ScopePermission('orders:create|approve')])
        class OrderController:
            # User needs create OR approve on orders
            pass

        @api_controller('/articles', permissions=[ScopePermission('articles:publish:editor')])
        class EditorArticleController:
            # User needs publish via editor role on articles
            pass
    """

    def __init__(self, perm: str, ctx: Optional[dict] = None):
        """
        Initialize the permission checker.

        Args:
            perm: Permission string in format
                  ``<scope>:<action1>/<action2>[:<role>][?context]`` or
                  ``<scope>:<action1>|<action2>[:<role>][?context]``
            ctx: Optional additional context dict (merged with query params).
        """
        self.perm = perm
        self.ctx = ctx if ctx else dict()

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        """
        Check if the user has the required permission.

        Handles both AND (``/``) and OR (``|``) operators automatically.
        """
        return str_check(request.user, self.perm, **self.ctx)


class ScopeAnyPermission(BasePermission):
    """
    Permission class for checking if user has at least one of multiple permissions.

    Each permission string can use ``/`` (AND) or ``|`` (OR) internally,
    and the overall check is OR across all provided strings.

    Example:
        @api_controller('/orders', permissions=[
            ScopeAnyPermission('orders:create|approve', 'articles:read')
        ])
        class MultiScopeController:
            # User needs (create OR approve on orders) OR (read on articles)
            pass
    """

    def __init__(self, *perms: str):
        """
        Initialize the permission checker with multiple permission strings.

        Args:
            *perms: Variable number of permission strings.
        """
        if not perms:
            raise ValueError("At least one permission string must be provided")
        self.perms = perms

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        """
        Check if the user has at least one of the required permissions.
        """
        from oxutils.permissions.caches import cache_any_permission_check

        return cache_any_permission_check(request.user, *self.perms)


class ScopeAnyActionPermission(BasePermission):
    """
    Permission class for checking if user has at least one of multiple actions
    on a **single scope** (OR semantics).

    This class forces OR semantics regardless of the separator in the string.
    Use ``ScopePermission`` with ``|`` separator if you want inline OR,
    or this class if you prefer explicit semantics.

    Example:
        @api_controller('/orders', permissions=[
            ScopeAnyActionPermission('orders:create/approve')
        ])
        class OrderController:
            # User needs create OR approve on orders (OR despite '/')
            pass

        @api_controller('/orders', permissions=[
            ScopeAnyActionPermission('orders:create|approve:manager')
        ])
        class ManagerOrderController:
            # Same as above but with role filter
            pass
    """

    def __init__(self, perm: str, ctx: Optional[dict] = None):
        """
        Initialize the permission checker with a permission string.

        Args:
            perm: Permission string. Regardless of separator, OR is used.
            ctx: Optional additional context dict.
        """
        if not perm:
            raise ValueError("Permission string must be provided")

        self.perm = perm
        self.ctx = ctx if ctx else {}

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        """
        Check if the user has at least one of the required actions (always OR).
        """
        from oxutils.permissions.caches import cache_any_action_check
        from oxutils.permissions.utils import parse_permission

        scope, actions, _operator, role, query_context = parse_permission(self.perm)
        final_context = {**query_context, **self.ctx}

        # Always OR regardless of the separator in the string
        return cache_any_action_check(request.user, scope, actions, role=role, **final_context)


def access_manager(actions: str):
    """
    Factory function for creating ScopePermission instances for access manager.

    Uses settings with a default for the scope (no mandatory config):
    - ACCESS_MANAGER_SCOPE: The scope to check (default ``"access"``)
    - ACCESS_MANAGER_GROUP: Optional group for UserGroup assignment
    - ACCESS_MANAGER_ROLE: Optional role filter for permission checks
    - ACCESS_MANAGER_CONTEXT: Optional context dict converted to query params

    Args:
        actions: Actions required.
                 Use ``/`` for AND (e.g., ``'create/approve'``)
                 or ``|`` for OR (e.g., ``'create|approve'``)

    Returns:
        ScopePermission instance configured with access manager settings

    Raises:
        ImproperlyConfigured: If ACCESS_MANAGER_CONTEXT is not a dict.

    Example:
        @api_controller('/access', permissions=[access_manager('write')])
        class AccessController:
            pass

        @api_controller('/access', permissions=[access_manager('read/write')])
        class AdvancedAccessController:
            # User needs both read AND write on access scope
            pass
    """
    # Scope defaults to "access" — the module owns this scope
    scope = getattr(settings, "ACCESS_MANAGER_SCOPE", "access")
    role = getattr(settings, "ACCESS_MANAGER_ROLE", None)
    ctx = getattr(settings, "ACCESS_MANAGER_CONTEXT", None)

    # Build base permission string: scope:actions
    perm = f"{scope}:{actions}"

    # Add role if defined and not None
    if role is not None:
        perm += f":{role}"

    # Get context if defined and not empty
    context = {}
    if ctx:
        context = ctx
        if not isinstance(context, dict):
            raise ImproperlyConfigured(
                "ACCESS_MANAGER_CONTEXT must be a dictionary. "
                f"Got {type(context).__name__} instead."
            )

    return ScopePermission(perm, context)


@lru_cache(maxsize=1)
def extra_permissions():
    """
    Return the list of permission instances defined in
    ``EXTRA_PERMISSIONS`` (settings.py).

    Each entry is a dotted path to an **already instantiated** permission
    object (e.g. a module-level singleton).  The object is imported via
    :func:`django.utils.module_loading.import_string` and returned as-is.

    The result is cached via :func:`functools.lru_cache` so that
    ``import_string`` is only called once per process.

    Example::

        # myapp/permissions.py
        from ninja_extra.permissions import BasePermission

        class IsPremium(BasePermission):
            def has_permission(self, request, controller):
                return request.user.is_premium

        IsPremium = IsPremium()   # <-- singleton instance

        # settings.py
        EXTRA_PERMISSIONS = [
            "myapp.permissions.IsPremium",
        ]

        # controller
        from oxutils.permissions import extra_permissions

        @api_controller(
            "/api",
            permissions=[*extra_permissions(), ScopePermission("articles:read")],
        )
        class MyController:
            ...
    """
    paths = getattr(settings, "EXTRA_PERMISSIONS", [])
    if not isinstance(paths, (list, tuple)):
        raise ImproperlyConfigured(
            "EXTRA_PERMISSIONS must be a list or tuple of dotted paths."
        )
    instances = []
    for path in paths:
        try:
            instance = import_string(path)
        except ImportError as exc:
            raise ImproperlyConfigured(
                f"Cannot import permission from EXTRA_PERMISSIONS: {path}"
            ) from exc
        instances.append(instance)
    return instances
