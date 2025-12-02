from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _



class OxutilsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'oxutils'
    verbose_name = _("Oxiliere Utilities")

    def ready(self):
        import oxutils.logger.receivers
        
        return super().ready()
