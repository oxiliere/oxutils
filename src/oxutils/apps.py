from django.apps import AppConfig


class OxutilsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'oxutils'

    def ready(self):
        import oxutils.logger.receivers
        
        return super().ready()