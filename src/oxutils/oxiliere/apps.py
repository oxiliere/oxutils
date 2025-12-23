from django.apps import AppConfig


class OxiliereConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'oxutils.oxiliere'

    def ready(self):
        import oxutils.oxiliere.caches
