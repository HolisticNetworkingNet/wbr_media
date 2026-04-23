from django.apps import AppConfig

class WbrMediaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wbr_media"
    verbose_name = "WBR Media"

    def ready(self):
        import wbr_media.signals

default_app_config = "wbr_media.apps.WbrMediaConfig"
