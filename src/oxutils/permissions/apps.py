from django.apps import AppConfig
from django.conf import settings


class PermissionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "oxutils.permissions"

    def ready(self):
        """Import checks when app is ready."""
        from . import checks  # noqa

        from .presets import (
            register_preset,
            register_access_scopes,
            register_access_applications,
        )

        if hasattr(settings, "PERMISSION_PRESET"):
            register_preset(settings.PERMISSION_PRESET)

        register_access_applications()
        register_access_scopes()
