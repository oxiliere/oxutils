"""
Django system checks for permissions configuration.

Example configuration in settings.py:

    ACCESS_MANAGER_SCOPE = "access"
    ACCESS_MANAGER_GROUP = "manager"  # or None
    ACCESS_MANAGER_ROLE = "admin"     # or None
    ACCESS_MANAGER_CONTEXT = {}

    ACCESS_APPLICATIONS = [
        "crm",
        "oxutils"
    ]

    CACHE_CHECK_PERMISSION = False

    ACCESS_SCOPES = [
        "users",
        "articles",
        "comments"
    ]

    PERMISSION_PRESET = {
        "roles": [...],
        "groups": [...],
        "role_grants": [...]
    }
"""

from django.conf import settings
from django.core.checks import Error, Tags, Warning, register


@register(Tags.security)
def check_permission_settings(app_configs, **kwargs):
    """
    Validate permission-related settings.

    Checks:
    - ACCESS_MANAGER_SCOPE is defined
    - ACCESS_MANAGER_GROUP is defined (can be None)
    - ACCESS_MANAGER_ROLE is defined (can be None)
    - ACCESS_MANAGER_CONTEXT is defined
    - ACCESS_SCOPES is defined
    - PERMISSION_PRESET is defined
    - ACCESS_APPLICATIONS is a list (if defined)
    - ACCESS_MANAGER_SCOPE exists in ACCESS_SCOPES
    - ACCESS_MANAGER_GROUP exists in PERMISSION_PRESET groups (if not None)
    - ACCESS_MANAGER_ROLE exists in PERMISSION_PRESET roles (if not None)
    - PERMISSION_PRESET roles/groups with 'app' have their app in ACCESS_APPLICATIONS
    """
    errors = []

    # Check ACCESS_MANAGER_SCOPE — optional, defaults to "access"
    if not hasattr(settings, 'ACCESS_MANAGER_SCOPE'):
        errors.append(
            Warning(
                'ACCESS_MANAGER_SCOPE is not defined (defaulting to "access")',
                hint='Add ACCESS_MANAGER_SCOPE = "access" to your settings to be explicit.',
                id='permissions.W003',
            )
        )

    # Check ACCESS_MANAGER_GROUP
    if not hasattr(settings, "ACCESS_MANAGER_GROUP"):
        errors.append(
            Error(
                "ACCESS_MANAGER_GROUP is not defined",
                hint='Add ACCESS_MANAGER_GROUP = "manager" or None to your settings',
                id="permissions.E002",
            )
        )

    # Check ACCESS_MANAGER_ROLE
    if not hasattr(settings, "ACCESS_MANAGER_ROLE"):
        errors.append(
            Error(
                "ACCESS_MANAGER_ROLE is not defined",
                hint='Add ACCESS_MANAGER_ROLE = "admin" or None to your settings',
                id="permissions.E013",
            )
        )

    # Check ACCESS_MANAGER_CONTEXT
    if not hasattr(settings, "ACCESS_MANAGER_CONTEXT"):
        errors.append(
            Error(
                "ACCESS_MANAGER_CONTEXT is not defined",
                hint="Add ACCESS_MANAGER_CONTEXT = {} to your settings",
                id="permissions.E003",
            )
        )

    # Check ACCESS_SCOPES
    if not hasattr(settings, 'ACCESS_SCOPES'):
        errors.append(
            Error(
                'ACCESS_SCOPES is not defined',
                hint='Add ACCESS_SCOPES = ["users", "articles", ...] to your settings',
                id='permissions.E004',
            )
        )
    else:
        # Validate ACCESS_SCOPES is a list (of strings or dicts)
        if not isinstance(settings.ACCESS_SCOPES, list):
            errors.append(
                Error(
                    'ACCESS_SCOPES must be a list',
                    hint='Set ACCESS_SCOPES = ["users", "articles", ...] or '
                         '[{"key": "...", "label": _("...")}, ...]',
                    id='permissions.E005',
                )
            )

    # Check PERMISSION_PRESET
    if not hasattr(settings, "PERMISSION_PRESET"):
        errors.append(
            Warning(
                "PERMISSION_PRESET is not defined",
                hint="Add PERMISSION_PRESET dict to your settings or use load_permission_preset",
                id="permissions.W001",
            )
        )
    else:
        # Validate PERMISSION_PRESET structure
        preset = settings.PERMISSION_PRESET
        if not isinstance(preset, dict):
            errors.append(
                Error(
                    "PERMISSION_PRESET must be a dictionary",
                    id="permissions.E006",
                )
            )
        else:
            # Check required keys
            required_keys = ["roles", "groups", "role_grants"]
            for key in required_keys:
                if key not in preset:
                    errors.append(
                        Error(
                            f"PERMISSION_PRESET is missing required key: {key}",
                            hint=f'Add "{key}" key to PERMISSION_PRESET',
                            id="permissions.E007",
                        )
                    )

            # Validate that actions used in role_grants exist in the preset
            if "actions" in preset and isinstance(preset["actions"], dict):
                all_defined_actions: set[str] = set()
                for scope_actions in preset["actions"].values():
                    if isinstance(scope_actions, dict):
                        all_defined_actions.update(scope_actions.keys())

                for rg in preset.get("role_grants", []):
                    rg_actions = rg.get("actions", [])
                    for action in rg_actions:
                        if action not in all_defined_actions:
                            errors.append(
                                Warning(
                                    f'Action "{action}" in role_grant (role={rg.get("role")}, '
                                    f"scope={rg.get('scope')}) is not defined in "
                                    f'PERMISSION_PRESET["actions"]',
                                    hint=f'Add "{action}" to PERMISSION_PRESET["actions"]["scope"]',
                                    id="permissions.W002",
                                )
                            )

    # Check ACCESS_APPLICATIONS (optional, but must be a list if defined)
    has_applications = hasattr(settings, "ACCESS_APPLICATIONS")
    if has_applications:
        if not isinstance(settings.ACCESS_APPLICATIONS, list):
            errors.append(
                Error(
                    "ACCESS_APPLICATIONS must be a list",
                    hint='Set ACCESS_APPLICATIONS = ["crm", "accounting", ...]',
                    id="permissions.E015",
                )
            )
            has_applications = False

    # Cross-validation: ACCESS_MANAGER_SCOPE in ACCESS_SCOPES — warning only
    # (the module owns the "access" scope via its permissions.py)
    if (
        hasattr(settings, "ACCESS_MANAGER_SCOPE")
        and hasattr(settings, "ACCESS_SCOPES")
        and isinstance(settings.ACCESS_SCOPES, list)
    ):
        scope_keys = {
            s["key"] if isinstance(s, dict) else str(s)
            for s in settings.ACCESS_SCOPES
        }
        if settings.ACCESS_MANAGER_SCOPE not in scope_keys:
            errors.append(
                Warning(
                    f'ACCESS_MANAGER_SCOPE "{settings.ACCESS_MANAGER_SCOPE}" is not in ACCESS_SCOPES',
                    hint=f'Add "{settings.ACCESS_MANAGER_SCOPE}" to ACCESS_SCOPES list if you '
                         f'want it visible in the frontend. The module manages it internally.',
                    id="permissions.W004",
                )
            )

    # Cross-validation: ACCESS_MANAGER_GROUP in PERMISSION_PRESET groups
    if (
        hasattr(settings, "ACCESS_MANAGER_GROUP")
        and settings.ACCESS_MANAGER_GROUP is not None
        and hasattr(settings, "PERMISSION_PRESET")
        and isinstance(settings.PERMISSION_PRESET, dict)
        and "groups" in settings.PERMISSION_PRESET
    ):
        group_slugs = [g.get("slug") for g in settings.PERMISSION_PRESET.get("groups", [])]

        if settings.ACCESS_MANAGER_GROUP not in group_slugs:
            errors.append(
                Error(
                    f'ACCESS_MANAGER_GROUP "{settings.ACCESS_MANAGER_GROUP}" is not in PERMISSION_PRESET groups',
                    hint=f'Add a group with slug "{settings.ACCESS_MANAGER_GROUP}" to PERMISSION_PRESET["groups"]',
                    id="permissions.E009",
                )
            )

    # Cross-validation: ACCESS_MANAGER_ROLE in PERMISSION_PRESET roles
    if (
        hasattr(settings, "ACCESS_MANAGER_ROLE")
        and settings.ACCESS_MANAGER_ROLE is not None
        and hasattr(settings, "PERMISSION_PRESET")
        and isinstance(settings.PERMISSION_PRESET, dict)
        and "roles" in settings.PERMISSION_PRESET
    ):
        role_slugs = [r.get("slug") for r in settings.PERMISSION_PRESET.get("roles", [])]

        if settings.ACCESS_MANAGER_ROLE not in role_slugs:
            errors.append(
                Error(
                    f'ACCESS_MANAGER_ROLE "{settings.ACCESS_MANAGER_ROLE}" is not in PERMISSION_PRESET roles',
                    hint=f'Add a role with slug "{settings.ACCESS_MANAGER_ROLE}" to PERMISSION_PRESET["roles"]',
                    id="permissions.E014",
                )
            )

    # Cross-validation: PERMISSION_PRESET roles/groups app values in ACCESS_APPLICATIONS
    if (
        has_applications
        and hasattr(settings, "PERMISSION_PRESET")
        and isinstance(settings.PERMISSION_PRESET, dict)
    ):
        apps_list = settings.ACCESS_APPLICATIONS

        for role_data in settings.PERMISSION_PRESET.get("roles", []):
            app = role_data.get("app")
            if app and app not in apps_list:
                errors.append(
                    Error(
                        f'Role "{role_data.get("slug")}" has app "{app}" which is not in ACCESS_APPLICATIONS',
                        hint=f'Add "{app}" to ACCESS_APPLICATIONS or remove "app" from this role',
                        id="permissions.E016",
                    )
                )

        for group_data in settings.PERMISSION_PRESET.get("groups", []):
            app = group_data.get("app")
            if app and app not in apps_list:
                errors.append(
                    Error(
                        f'Group "{group_data.get("slug")}" has app "{app}" which is not in ACCESS_APPLICATIONS',
                        hint=f'Add "{app}" to ACCESS_APPLICATIONS or remove "app" from this group',
                        id="permissions.E017",
                    )
                )

    # Cross-validation: scope ownership — each scope in actions must be unique across apps.
    # (Conflicts between settings.PERMISSION_PRESET and app presets are already caught
    #  by register_preset() which raises ImproperlyConfigured at startup.)
    if hasattr(settings, "PERMISSION_PRESET") and isinstance(settings.PERMISSION_PRESET, dict):
        scope_owners: dict[str, str] = {}

        from oxutils.permissions.presets import discover_app_presets

        for preset in discover_app_presets():
            app_label = preset.get("_app_label", "unknown")
            preset_actions = preset.get("actions", {})
            if not isinstance(preset_actions, dict):
                continue
            for scope in preset_actions:
                if scope in scope_owners:
                    errors.append(
                        Error(
                            f'Scope "{scope}" is defined in both '
                            f'"{scope_owners[scope]}" and "{app_label}". '
                            f'Each scope must be owned by exactly one app.',
                            hint=f'Remove the scope "{scope}" from one of the apps.',
                            id="permissions.E022",
                        )
                    )
                else:
                    scope_owners[scope] = app_label

    # Cross-validation: roles/groups with app require ACCESS_APPLICATIONS
    if (
        not has_applications
        and hasattr(settings, "PERMISSION_PRESET")
        and isinstance(settings.PERMISSION_PRESET, dict)
    ):
        has_app_attr = False
        for role_data in settings.PERMISSION_PRESET.get("roles", []):
            if role_data.get("app"):
                has_app_attr = True
                break

        if not has_app_attr:
            for group_data in settings.PERMISSION_PRESET.get("groups", []):
                if group_data.get("app"):
                    has_app_attr = True
                    break

        if has_app_attr:
            errors.append(
                Error(
                    'ACCESS_APPLICATIONS is required when roles or groups define an "app" attribute',
                    hint='Add ACCESS_APPLICATIONS = ["crm", "oxutils", ...] to your settings',
                    id="permissions.E018",
                )
            )

    # Validate ACCESS_MANAGER_CONTEXT is a dict
    if hasattr(settings, "ACCESS_MANAGER_CONTEXT"):
        if not isinstance(settings.ACCESS_MANAGER_CONTEXT, dict):
            errors.append(
                Error(
                    "ACCESS_MANAGER_CONTEXT must be a dictionary",
                    hint="Set ACCESS_MANAGER_CONTEXT = {}",
                    id="permissions.E010",
                )
            )

    # Check CACHE_CHECK_PERMISSION and cacheops dependency
    if hasattr(settings, "CACHE_CHECK_PERMISSION") and settings.CACHE_CHECK_PERMISSION:
        if not hasattr(settings, "INSTALLED_APPS"):
            errors.append(
                Error(
                    "INSTALLED_APPS is not defined",
                    id="permissions.E011",
                )
            )
        elif "cacheops" not in settings.INSTALLED_APPS:
            errors.append(
                Error(
                    "CACHE_CHECK_PERMISSION is True but cacheops is not in INSTALLED_APPS",
                    hint='Add "cacheops" to INSTALLED_APPS or set CACHE_CHECK_PERMISSION = False',
                    id="permissions.E012",
                )
            )

    # Validate EXTRA_PERMISSIONS
    if hasattr(settings, "EXTRA_PERMISSIONS"):
        extra = settings.EXTRA_PERMISSIONS
        if not isinstance(extra, (list, tuple)):
            errors.append(
                Error(
                    "EXTRA_PERMISSIONS must be a list or tuple",
                    hint='Set EXTRA_PERMISSIONS = ["dotted.path.ToPermission", ...]',
                    id="permissions.E019",
                )
            )
        else:
            from django.utils.module_loading import import_string

            for path in extra:
                if not isinstance(path, str):
                    errors.append(
                        Error(
                            f"Each entry in EXTRA_PERMISSIONS must be a string, got {type(path).__name__}",
                            hint='Use dotted paths like "myapp.permissions.MyPermission"',
                            id="permissions.E020",
                        )
                    )
                    continue
                try:
                    import_string(path)
                except ImportError:
                    errors.append(
                        Error(
                            f'Cannot import "{path}" from EXTRA_PERMISSIONS',
                            hint="Check that the module and class exist",
                            id="permissions.E021",
                        )
                    )
                    continue

    return errors
