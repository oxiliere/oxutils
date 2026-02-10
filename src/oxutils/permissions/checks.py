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
        "group": [...],
        "role_grants": [...]
    }
"""

from django.conf import settings
from django.core.checks import Error, Warning, register, Tags


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
    
    # Check ACCESS_MANAGER_SCOPE
    if not hasattr(settings, 'ACCESS_MANAGER_SCOPE'):
        errors.append(
            Error(
                'ACCESS_MANAGER_SCOPE is not defined',
                hint='Add ACCESS_MANAGER_SCOPE = "access" to your settings',
                id='permissions.E001',
            )
        )
    
    # Check ACCESS_MANAGER_GROUP
    if not hasattr(settings, 'ACCESS_MANAGER_GROUP'):
        errors.append(
            Error(
                'ACCESS_MANAGER_GROUP is not defined',
                hint='Add ACCESS_MANAGER_GROUP = "manager" or None to your settings',
                id='permissions.E002',
            )
        )
    
    # Check ACCESS_MANAGER_ROLE
    if not hasattr(settings, 'ACCESS_MANAGER_ROLE'):
        errors.append(
            Error(
                'ACCESS_MANAGER_ROLE is not defined',
                hint='Add ACCESS_MANAGER_ROLE = "admin" or None to your settings',
                id='permissions.E013',
            )
        )
    
    # Check ACCESS_MANAGER_CONTEXT
    if not hasattr(settings, 'ACCESS_MANAGER_CONTEXT'):
        errors.append(
            Error(
                'ACCESS_MANAGER_CONTEXT is not defined',
                hint='Add ACCESS_MANAGER_CONTEXT = {} to your settings',
                id='permissions.E003',
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
        # Validate ACCESS_SCOPES is a list
        if not isinstance(settings.ACCESS_SCOPES, list):
            errors.append(
                Error(
                    'ACCESS_SCOPES must be a list',
                    hint='Set ACCESS_SCOPES = ["users", "articles", ...]',
                    id='permissions.E005',
                )
            )
    
    # Check PERMISSION_PRESET
    if not hasattr(settings, 'PERMISSION_PRESET'):
        errors.append(
            Warning(
                'PERMISSION_PRESET is not defined',
                hint='Add PERMISSION_PRESET dict to your settings or use load_permission_preset',
                id='permissions.W001',
            )
        )
    else:
        # Validate PERMISSION_PRESET structure
        preset = settings.PERMISSION_PRESET
        if not isinstance(preset, dict):
            errors.append(
                Error(
                    'PERMISSION_PRESET must be a dictionary',
                    id='permissions.E006',
                )
            )
        else:
            # Check required keys
            required_keys = ['roles', 'group', 'role_grants']
            for key in required_keys:
                if key not in preset:
                    errors.append(
                        Error(
                            f'PERMISSION_PRESET is missing required key: {key}',
                            hint=f'Add "{key}" key to PERMISSION_PRESET',
                            id=f'permissions.E007',
                        )
                    )
    
    # Check ACCESS_APPLICATIONS (optional, but must be a list if defined)
    has_applications = hasattr(settings, 'ACCESS_APPLICATIONS')
    if has_applications:
        if not isinstance(settings.ACCESS_APPLICATIONS, list):
            errors.append(
                Error(
                    'ACCESS_APPLICATIONS must be a list',
                    hint='Set ACCESS_APPLICATIONS = ["crm", "accounting", ...]',
                    id='permissions.E015',
                )
            )
            has_applications = False
    
    # Cross-validation: ACCESS_MANAGER_SCOPE in ACCESS_SCOPES
    if (hasattr(settings, 'ACCESS_MANAGER_SCOPE') and 
        hasattr(settings, 'ACCESS_SCOPES') and 
        isinstance(settings.ACCESS_SCOPES, list)):
        
        if settings.ACCESS_MANAGER_SCOPE not in settings.ACCESS_SCOPES:
            errors.append(
                Error(
                    f'ACCESS_MANAGER_SCOPE "{settings.ACCESS_MANAGER_SCOPE}" is not in ACCESS_SCOPES',
                    hint=f'Add "{settings.ACCESS_MANAGER_SCOPE}" to ACCESS_SCOPES list',
                    id='permissions.E008',
                )
            )
    
    # Cross-validation: ACCESS_MANAGER_GROUP in PERMISSION_PRESET groups
    if (hasattr(settings, 'ACCESS_MANAGER_GROUP') and 
        settings.ACCESS_MANAGER_GROUP is not None and
        hasattr(settings, 'PERMISSION_PRESET') and
        isinstance(settings.PERMISSION_PRESET, dict) and
        'group' in settings.PERMISSION_PRESET):
        
        group_slugs = [g.get('slug') for g in settings.PERMISSION_PRESET.get('group', [])]
        
        if settings.ACCESS_MANAGER_GROUP not in group_slugs:
            errors.append(
                Error(
                    f'ACCESS_MANAGER_GROUP "{settings.ACCESS_MANAGER_GROUP}" is not in PERMISSION_PRESET groups',
                    hint=f'Add a group with slug "{settings.ACCESS_MANAGER_GROUP}" to PERMISSION_PRESET["group"]',
                    id='permissions.E009',
                )
            )
    
    # Cross-validation: ACCESS_MANAGER_ROLE in PERMISSION_PRESET roles
    if (hasattr(settings, 'ACCESS_MANAGER_ROLE') and 
        settings.ACCESS_MANAGER_ROLE is not None and
        hasattr(settings, 'PERMISSION_PRESET') and
        isinstance(settings.PERMISSION_PRESET, dict) and
        'roles' in settings.PERMISSION_PRESET):
        
        role_slugs = [r.get('slug') for r in settings.PERMISSION_PRESET.get('roles', [])]
        
        if settings.ACCESS_MANAGER_ROLE not in role_slugs:
            errors.append(
                Error(
                    f'ACCESS_MANAGER_ROLE "{settings.ACCESS_MANAGER_ROLE}" is not in PERMISSION_PRESET roles',
                    hint=f'Add a role with slug "{settings.ACCESS_MANAGER_ROLE}" to PERMISSION_PRESET["roles"]',
                    id='permissions.E014',
                )
            )
    
    # Cross-validation: PERMISSION_PRESET roles/groups app values in ACCESS_APPLICATIONS
    if (has_applications and
        hasattr(settings, 'PERMISSION_PRESET') and
        isinstance(settings.PERMISSION_PRESET, dict)):
        
        apps_list = settings.ACCESS_APPLICATIONS
        
        for role_data in settings.PERMISSION_PRESET.get('roles', []):
            app = role_data.get('app')
            if app and app not in apps_list:
                errors.append(
                    Error(
                        f'Role "{role_data.get("slug")}" has app "{app}" which is not in ACCESS_APPLICATIONS',
                        hint=f'Add "{app}" to ACCESS_APPLICATIONS or remove "app" from this role',
                        id='permissions.E016',
                    )
                )
        
        for group_data in settings.PERMISSION_PRESET.get('group', []):
            app = group_data.get('app')
            if app and app not in apps_list:
                errors.append(
                    Error(
                        f'Group "{group_data.get("slug")}" has app "{app}" which is not in ACCESS_APPLICATIONS',
                        hint=f'Add "{app}" to ACCESS_APPLICATIONS or remove "app" from this group',
                        id='permissions.E017',
                    )
                )
    
    # Cross-validation: roles/groups with app require ACCESS_APPLICATIONS
    if (not has_applications and
        hasattr(settings, 'PERMISSION_PRESET') and
        isinstance(settings.PERMISSION_PRESET, dict)):
        
        has_app_attr = False
        for role_data in settings.PERMISSION_PRESET.get('roles', []):
            if role_data.get('app'):
                has_app_attr = True
                break
        
        if not has_app_attr:
            for group_data in settings.PERMISSION_PRESET.get('group', []):
                if group_data.get('app'):
                    has_app_attr = True
                    break
        
        if has_app_attr:
            errors.append(
                Error(
                    'ACCESS_APPLICATIONS is required when roles or groups define an "app" attribute',
                    hint='Add ACCESS_APPLICATIONS = ["crm", "oxutils", ...] to your settings',
                    id='permissions.E018',
                )
            )
    
    # Validate ACCESS_MANAGER_CONTEXT is a dict
    if hasattr(settings, 'ACCESS_MANAGER_CONTEXT'):
        if not isinstance(settings.ACCESS_MANAGER_CONTEXT, dict):
            errors.append(
                Error(
                    'ACCESS_MANAGER_CONTEXT must be a dictionary',
                    hint='Set ACCESS_MANAGER_CONTEXT = {}',
                    id='permissions.E010',
                )
            )
    
    # Check CACHE_CHECK_PERMISSION and cacheops dependency
    if hasattr(settings, 'CACHE_CHECK_PERMISSION') and settings.CACHE_CHECK_PERMISSION:
        if not hasattr(settings, 'INSTALLED_APPS'):
            errors.append(
                Error(
                    'INSTALLED_APPS is not defined',
                    id='permissions.E011',
                )
            )
        elif 'cacheops' not in settings.INSTALLED_APPS:
            errors.append(
                Error(
                    'CACHE_CHECK_PERMISSION is True but cacheops is not in INSTALLED_APPS',
                    hint='Add "cacheops" to INSTALLED_APPS or set CACHE_CHECK_PERMISSION = False',
                    id='permissions.E012',
                )
            )
    
    return errors
