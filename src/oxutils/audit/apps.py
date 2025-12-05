from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _



class OxutilsAuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'oxutils.audit'
    verbose_name = _("Oxutils Audit")

    def ready(self):
        return super().ready()
