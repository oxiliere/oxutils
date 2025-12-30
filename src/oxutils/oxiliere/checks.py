"""
Check TENANT_MODEL & TENANT_USER_MODEL
"""
from django.conf import settings
from django.core.checks import Error, register, Tags


@register(Tags.models)
def check_tenant_settings(app_configs, **kwargs):
    """Check that TENANT_MODEL and TENANT_USER_MODEL are defined in settings."""
    errors = []
    
    if not hasattr(settings, 'TENANT_MODEL'):
        errors.append(
            Error(
                'TENANT_MODEL is not defined in settings',
                hint='Add TENANT_MODEL = "app_label.ModelName" to your settings',
                id='oxiliere.E001',
            )
        )
    
    if not hasattr(settings, 'TENANT_USER_MODEL'):
        errors.append(
            Error(
                'TENANT_USER_MODEL is not defined in settings',
                hint='Add TENANT_USER_MODEL = "app_label.ModelName" to your settings',
                id='oxiliere.E002',
            )
        )
    
    return errors