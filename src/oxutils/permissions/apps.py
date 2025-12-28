from django.apps import AppConfig


class PermissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'oxutils.permissions'
    
    def ready(self):
        """Import checks when app is ready."""
        from . import checks  # noqa
