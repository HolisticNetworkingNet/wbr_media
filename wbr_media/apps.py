from django.apps import AppConfig

class WbrMediaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wbr_media"
    verbose_name = "WBR Media"

default_app_config = "wbr_media.apps.WbrMediaConfig"
